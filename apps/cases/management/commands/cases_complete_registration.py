from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from django.utils import timezone
from apps.cases.models import Case, CaseDevice, CaseProcedure
from apps.cases.services.case_service import CaseService
from apps.core.middleware import set_current_user


class Command(BaseCommand):
    help = "Busca cases com pelo menos 1 device e 1 procedure que tenham registration_completed_at None e executa a lógica de complete registration"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa apenas a busca sem completar o registro (modo de teste)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limita o número de cases a processar (padrão: sem limite). Exemplo: --limit 10',
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
            help='Login do usuário para atribuir os cases após completar o registro (opcional)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options.get('limit')
        username = options['username']
        assign_to_username = options.get('assign_to')
        
        # Validar usuário que executou a operação (assigned_by)
        try:
            from django.contrib.auth.models import User
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
        
        # Inicializar o service com o usuário
        case_service = CaseService(user=assigned_by_user)

        # Buscar cases que atendem aos critérios
        self.stdout.write("🔍 Buscando cases elegíveis para complete registration...")
        
        # Diagnóstico: contar cases sem registration_completed_at
        total_cases_no_registration = Case.objects.filter(
            registration_completed_at__isnull=True
        ).count()
        self.stdout.write(f"📊 Cases sem registration_completed_at: {total_cases_no_registration}")
        
        # Query para buscar cases com:
        # - registration_completed_at is None (não completados)
        # - deleted_at is None (não deletados)
        # - pelo menos 1 device ATIVO (case_devices não deletado)
        # - pelo menos 1 procedure ATIVO (procedures não deletado)
        from django.db.models import Q, Count
        
        eligible_cases = Case.objects.filter(
            registration_completed_at__isnull=True,
            deleted_at__isnull=True  # Apenas cases não deletados
        ).annotate(
            device_count=Count(
                'case_devices',
                filter=Q(case_devices__deleted_at__isnull=True)
            ),
            procedure_count=Count(
                'procedures',
                filter=Q(procedures__deleted_at__isnull=True)
            )
        ).filter(
            device_count__gte=1,
            procedure_count__gte=1
        ).select_related(
            'extraction_unit',
            'requester_agency_unit',
            'requester_authority_position',
            'crime_category'
        )
        
        # Diagnóstico adicional
        total_before_count = eligible_cases.count()
        self.stdout.write(f"📊 Cases elegíveis (antes do count final): {total_before_count}")
        
        # Mostrar alguns exemplos para debug
        if total_before_count == 0:
            # Verificar cases com devices/documents mas sem contar corretamente
            debug_cases = Case.objects.filter(
                registration_completed_at__isnull=True,
                deleted_at__isnull=True
            )[:5]
            
            for case in debug_cases:
                # Contar apenas não deletados
                device_count_active = CaseDevice.objects.filter(case=case, deleted_at__isnull=True).count()
                procedure_count_active = CaseProcedure.objects.filter(case=case, deleted_at__isnull=True).count()
                device_count_all = CaseDevice.objects.filter(case=case).count()
                procedure_count_all = CaseProcedure.objects.filter(case=case).count()
                
                self.stdout.write(
                    f"🔍 Case ID {case.id}: devices ativos={device_count_active} (total={device_count_all}), "
                    f"procedures ativos={procedure_count_active} (total={procedure_count_all})"
                )

        # Contar antes de aplicar limite
        total_cases = eligible_cases.count()
        
        # Aplicar limite se especificado (após o count)
        if limit:
            eligible_cases = eligible_cases[:limit]
            self.stdout.write(f"🔢 Limite aplicado: máximo {limit} cases (encontrados: {total_cases})")
        
        if total_cases == 0:
            self.stdout.write(
                self.style.WARNING("⚠️  Nenhum case elegível encontrado.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"✅ Encontrados {total_cases} cases elegíveis")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🧪 MODO DRY-RUN: Nenhuma alteração será feita")
            )
            
            # Mostrar detalhes dos cases encontrados
            for case in eligible_cases:
                self.stdout.write(
                    f"📋 Case ID: {case.id} | "
                    f"Devices: {case.device_count} | "
                    f"Procedures: {case.procedure_count} | "
                    f"Status: {case.status} | "
                    f"Extraction Unit: {case.extraction_unit.name if case.extraction_unit else 'N/A'}"
                )
            return

        # Processar os cases
        processed_count = 0
        success_count = 0
        error_count = 0
        errors = []

        self.stdout.write("🚀 Iniciando processamento dos cases...")

        for case in eligible_cases:
            try:
                with transaction.atomic():
                    # Completar o registro primeiro
                    updated_case = case_service.complete_registration(case.id)
                    
                    # Se --assign-to foi informado, atribuir o case ao usuário
                    if assign_to_user:
                        updated_case = case_service.assign_to_user(
                            case_pk=updated_case.id,
                            user=assign_to_user
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Case {case.id} completado e atribuído a {assign_to_user.username} "
                                f"(por {assigned_by_user.username}) - Número: {updated_case.number if updated_case.number else 'N/A'}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Case {case.id} completado (por {assigned_by_user.username}) - Número: {updated_case.number if updated_case.number else 'N/A'}"
                            )
                        )
                    
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                error_msg = f"❌ Erro ao processar case {case.id}: {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
            
            processed_count += 1

        # Relatório final
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 RELATÓRIO FINAL")
        self.stdout.write("="*60)
        self.stdout.write(f"📋 Total de cases encontrados: {total_cases}")
        if limit:
            self.stdout.write(f"🔢 Limite aplicado: {limit}")
        self.stdout.write(f"🔄 Total processados: {processed_count}")
        self.stdout.write(f"✅ Sucessos: {success_count}")
        self.stdout.write(f"❌ Erros: {error_count}")
        self.stdout.write(f"👤 Operação executada por: {assigned_by_user.username}")
        
        if assign_to_user:
            self.stdout.write(f"👤 Cases atribuídos a: {assign_to_user.username}")
        
        if errors:
            self.stdout.write("\n🚨 ERROS ENCONTRADOS:")
            for error in errors:
                self.stdout.write(f"   {error}")
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 {success_count} cases foram completados com sucesso!")
            )
