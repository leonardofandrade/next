from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from django.utils import timezone
from django.contrib.auth.models import User
from apps.cases.models import Case, Extraction
from apps.cases.services.case_service import CaseService
from apps.cases.services.extraction_service import ExtractionService
from apps.configs.services.extractor_service import check_user_assignment_to_unit
from apps.core.middleware import set_current_user


class Command(BaseCommand):
    help = "Busca casos com dispositivos mas sem extrações e cria extrações para eles"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa apenas a busca sem criar extrações (modo de teste)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limita o número de casos a processar (padrão: sem limite). Exemplo: --limit 10',
        )
        parser.add_argument(
            '--u',
            type=str,
            dest='username',
            help='Login do usuário que executou a operação (assigned_by) - obrigatório',
            required=True
        )
        parser.add_argument(
            '--assign-to',
            type=str,
            dest='assign_to',
            help='Login do usuário para atribuir as extrações criadas (opcional)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options.get('limit')
        username = options['username']
        assign_to_username = options.get('assign_to')
        
        # Validar usuário que executou a operação (assigned_by)
        try:
            assigned_by_user = User.objects.select_related('profile').get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Usuário com login '{username}' não encontrado")
        
        # Validar usuário para atribuição se fornecido
        assign_to_user = None
        if assign_to_username:
            try:
                assign_to_user = User.objects.select_related('profile').get(username=assign_to_username)
                # Verificar se o usuário é extrator (apenas aviso, não erro)
                if not hasattr(assign_to_user, 'profile') or not assign_to_user.profile.is_extractor:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Aviso: Usuário '{assign_to_username}' não é um extrator")
                    )
            except User.DoesNotExist:
                raise CommandError(f"Usuário com login '{assign_to_username}' não encontrado")
        
        # Definir o usuário atual no thread-local para que os campos do AuditedModel sejam preenchidos
        set_current_user(assigned_by_user)

        # Inicializar os services
        case_service = CaseService(user=assigned_by_user)
        extraction_service = ExtractionService(user=assigned_by_user)

        # Buscar casos que atendem aos critérios
        self.stdout.write("🔍 Buscando casos elegíveis para criação de extrações...")
        
        # Query para buscar casos com:
        # - registration_completed_at não é None (casos completados)
        # - pelo menos 1 device (case_devices)
        # - sem extrações (case_devices sem device_extraction)
        eligible_cases = Case.objects.filter(
            registration_completed_at__isnull=False
        ).annotate(
            device_count=models.Count('case_devices'),
            extraction_count=models.Count('case_devices__device_extraction')
        ).filter(
            device_count__gte=1,
            extraction_count=0  # Sem extrações
        ).select_related(
            'extraction_unit',
            'requester_agency_unit',
            'requester_authority_position',
            'crime_type'
        ).prefetch_related('case_devices')

        # Aplicar limite se especificado
        if limit:
            eligible_cases = eligible_cases[:limit]
            self.stdout.write(f"🔢 Limite aplicado: máximo {limit} casos")

        total_cases = eligible_cases.count()
        
        if total_cases == 0:
            self.stdout.write(
                self.style.WARNING("⚠️  Nenhum caso elegível encontrado.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"✅ Encontrados {total_cases} casos elegíveis")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🧪 MODO DRY-RUN: Nenhuma extração será criada")
            )
            
            # Mostrar detalhes dos casos encontrados
            for case in eligible_cases:
                self.stdout.write(
                    f"📋 Caso ID: {case.id} | "
                    f"Número: {case.number} | "
                    f"Dispositivos: {case.device_count} | "
                    f"Status: {case.status} | "
                    f"Unidade: {case.extraction_unit.name if case.extraction_unit else 'N/A'}"
                )
            return

        # Processar os casos
        processed_count = 0
        success_count = 0
        error_count = 0
        total_extractions_created = 0
        errors = []

        self.stdout.write("🚀 Iniciando criação de extrações...")

        for case in eligible_cases:
            try:
                with transaction.atomic():
                    extractions_created = 0
                    
                    # Validar se o extrator está associado à extraction_unit do case (se assign_to foi informado)
                    assign_to_extractor_user = None
                    if assign_to_user and case.extraction_unit:
                        if hasattr(assign_to_user, 'profile') and assign_to_user.profile.is_extractor:
                            if not check_user_assignment_to_unit(assign_to_user, case.extraction_unit):
                                raise Exception(
                                    f"O extrator '{assign_to_user.username}' não está associado à "
                                    f"unidade de extração '{case.extraction_unit.name}' do case {case.id}"
                                )
                            # Buscar o ExtractorUser correspondente
                            from apps.core.models import ExtractorUser
                            try:
                                assign_to_extractor_user = ExtractorUser.objects.get(
                                    user=assign_to_user,
                                    deleted_at__isnull=True
                                )
                            except ExtractorUser.DoesNotExist:
                                raise Exception(
                                    f"Usuário '{assign_to_user.username}' não possui um ExtractorUser associado"
                                )
                    
                    # Criar extração para cada dispositivo do caso
                    for case_device in case.case_devices.all():
                        # Verificar se já existe extração para este dispositivo
                        if hasattr(case_device, 'device_extraction'):
                            self.stdout.write(
                                f"⚠️  Dispositivo {case_device.id} já possui extração, pulando..."
                            )
                            continue
                        
                        # Criar nova extração usando o service
                        extraction_data = {
                            'case_device': case_device,
                            'status': Extraction.STATUS_ASSIGNED if assign_to_extractor_user else Extraction.STATUS_PENDING,
                        }
                        
                        if assign_to_extractor_user:
                            extraction_data['assigned_to'] = assign_to_extractor_user
                            extraction_data['assigned_at'] = timezone.now()
                        
                        extraction = extraction_service.create(extraction_data)
                        
                        extractions_created += 1
                        total_extractions_created += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Extração {extraction.id} criada para dispositivo {case_device.id}"
                            )
                        )
                    
                    if extractions_created > 0:
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Caso {case.id} processado: {extractions_created} extração(ões) criada(s)"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️  Caso {case.id}: nenhuma extração criada (todas já existiam)"
                            )
                        )
                    
            except Exception as e:
                error_count += 1
                error_msg = f"❌ Erro ao processar caso {case.id}: {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
            
            processed_count += 1

        # Relatório final
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 RELATÓRIO FINAL")
        self.stdout.write("="*60)
        self.stdout.write(f"📋 Total de casos encontrados: {total_cases}")
        if limit:
            self.stdout.write(f"🔢 Limite aplicado: {limit}")
        self.stdout.write(f"🔄 Total processados: {processed_count}")
        self.stdout.write(f"✅ Casos processados com sucesso: {success_count}")
        self.stdout.write(f"❌ Casos com erro: {error_count}")
        self.stdout.write(f"🔧 Total de extrações criadas: {total_extractions_created}")
        self.stdout.write(f"👤 Operação executada por: {assigned_by_user.username}")
        
        if assign_to_user:
            self.stdout.write(f"👤 Extrações atribuídas a: {assign_to_user.username}")
        
        if errors:
            self.stdout.write("\n🚨 ERROS ENCONTRADOS:")
            for error in errors:
                self.stdout.write(f"   {error}")
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 {success_count} casos foram processados com sucesso!")
            )
            self.stdout.write(
                self.style.SUCCESS(f"🔧 {total_extractions_created} extrações foram criadas!")
            )
