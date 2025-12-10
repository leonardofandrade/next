from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from django.utils import timezone
from django.contrib.auth.models import User
from apps.cases.models import Case, Extraction
from apps.cases.services.extraction_service import ExtractionService
from apps.configs.services.extractor_service import check_user_assignment_to_unit, get_available_extractors, get_extractor_assignments_by_unit
from apps.core.middleware import set_current_user
import random


class Command(BaseCommand):
    help = "Inicia extrações de forma randomizada, atribuindo usuários extratores aleatoriamente"

    def add_arguments(self, parser):
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
            help='Login do usuário para atribuir as extrações (opcional - se não informado, usa o usuário da extração ou randomiza)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Número de extrações para processar (opcional). Exemplo: --limit 10',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Processa todas as extrações disponíveis (ignora --limit se especificado)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa apenas a busca sem iniciar extrações (modo de teste)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options.get('limit')
        process_all = options['all']
        username = options['username']
        assign_to_username = options.get('assign_to')
        
        # Validar parâmetros
        if process_all and limit:
            self.stdout.write(
                self.style.WARNING("[WARNING] --all especificado, ignorando --limit")
            )
            limit = None
        
        if not process_all and not limit:
            raise CommandError(
                "Você deve especificar --limit <número> ou --all para processar extrações"
            )

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
        
        # Inicializar o service com o usuário
        extraction_service = ExtractionService(user=assigned_by_user)

        # Buscar extrações elegíveis para iniciar
        self.stdout.write("[INFO] Buscando extrações elegíveis para iniciar...")
        
        # Query para buscar extrações com status ASSIGNED ou PENDING
        eligible_extractions = Extraction.objects.filter(
            status__in=[Extraction.STATUS_ASSIGNED, Extraction.STATUS_PENDING]
        ).select_related(
            'case_device',
            'case_device__case',
            'case_device__case__extraction_unit',
            'assigned_to'
        ).prefetch_related(
            'case_device__case__case_devices'
        )

        # Aplicar limite se especificado
        if limit:
            eligible_extractions = eligible_extractions[:limit]
            self.stdout.write(f"[INFO] Limite aplicado: máximo {limit} extrações")

        total_extractions = eligible_extractions.count()
        
        if total_extractions == 0:
            self.stdout.write(
                self.style.WARNING("[WARNING] Nenhuma extração elegível encontrada.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"[SUCCESS] Encontradas {total_extractions} extrações elegíveis")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("[DRY-RUN] MODO DRY-RUN: Nenhuma extração será iniciada")
            )
            
            # Mostrar detalhes das extrações encontradas
            for extraction in eligible_extractions:
                case = extraction.case_device.case
                self.stdout.write(
                    f"[INFO] Extração ID: {extraction.id} | "
                    f"Caso: {case.number} | "
                    f"Dispositivo: {extraction.case_device.id} | "
                    f"Status: {extraction.get_status_display()} | "
                    f"Atribuído a: {extraction.assigned_to.username if extraction.assigned_to else 'N/A'}"
                )
            return

        # Processar as extrações
        processed_count = 0
        success_count = 0
        error_count = 0
        errors = []

        self.stdout.write("[INFO] Iniciando extrações...")

        for extraction in eligible_extractions:
            try:
                with transaction.atomic():
                    case = extraction.case_device.case
                    
                    # Determinar qual usuário iniciará a extração
                    extraction_user = assign_to_user
                    
                    # Se não foi especificado um usuário, usar o assigned_to da extração ou buscar extratores da extraction_unit
                    if not extraction_user:
                        if extraction.assigned_to:
                            # Usar o usuário já atribuído à extração
                            extraction_user = extraction.assigned_to
                        elif case.extraction_unit:
                            # Buscar extratores associados à extraction_unit do case
                            assignments = get_extractor_assignments_by_unit(case.extraction_unit)
                            active_assignments = [
                                a.user for a in assignments 
                                if a.unassigned_at is None and a.user.is_active
                            ]
                            
                            if active_assignments:
                                extraction_user = random.choice(active_assignments)
                            else:
                                # Fallback: buscar todos os extratores disponíveis
                                fallback_extractors = list(get_available_extractors())
                                if not fallback_extractors:
                                    raise Exception(
                                        f"Nenhum extrator disponível para iniciar a extração {extraction.id}. "
                                        f"Unidade: {case.extraction_unit.name}"
                                    )
                                extraction_user = random.choice(fallback_extractors)
                        else:
                            # Fallback: buscar todos os extratores disponíveis
                            fallback_extractors = list(get_available_extractors())
                            if not fallback_extractors:
                                raise Exception(f"Nenhum extrator disponível para iniciar a extração {extraction.id}")
                            extraction_user = random.choice(fallback_extractors)
                    
                    # Validar se o extrator está associado à extraction_unit do case
                    if case.extraction_unit:
                        if hasattr(extraction_user, 'profile') and extraction_user.profile.is_extractor:
                            if not check_user_assignment_to_unit(extraction_user, case.extraction_unit):
                                raise Exception(
                                    f"O extrator '{extraction_user.username}' não está associado à "
                                    f"unidade de extração '{case.extraction_unit.name}' do case {case.id}"
                                )
                    
                    # Atribuir a extração ao usuário se ainda não estiver atribuída
                    if extraction.status == Extraction.STATUS_PENDING:
                        # Primeiro atribuir a extração usando o service
                        from apps.core.models import ExtractorUser
                        try:
                            extractor_user = ExtractorUser.objects.get(user=extraction_user, deleted_at__isnull=True)
                            extraction_service.user = assigned_by_user  # Definir usuário do service
                            extraction = extraction_service.assign_extraction(
                                extraction_pk=extraction.id,
                                extractor_user_pk=extractor_user.id
                            )
                        except ExtractorUser.DoesNotExist:
                            raise Exception(f"Usuário {extraction_user.username} não é um ExtractorUser válido")
                    
                    # Usar o service para iniciar a extração
                    # O service já valida se o usuário está associado à extraction_unit
                    updated_extraction = extraction_service.start_extraction(
                        extraction_pk=extraction.id
                    )
                    
                    # Adicionar notas se necessário usando o service
                    if hasattr(updated_extraction, 'started_notes'):
                        extraction_service.update(
                            pk=updated_extraction.id,
                            data={'started_notes': f"Extração iniciada por {assigned_by_user.username}"}
                        )
                    
                    success_count += 1
                    processed_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[SUCCESS] Extração {updated_extraction.id} iniciada - "
                            f"Caso: {case.number} | "
                            f"Dispositivo: {updated_extraction.case_device.id} | "
                            f"Extrator: {extraction_user.username} | "
                            f"Operação executada por: {assigned_by_user.username}"
                        )
                    )
                    
                    # Atualizar status do caso se necessário
                    if case.status in [Case.CASE_STATUS_WAITING_EXTRACTOR, Case.CASE_STATUS_WAITING_START]:
                        from apps.cases.services.case_service import CaseService
                        case_service = CaseService(user=assigned_by_user)
                        case_service.update(
                            pk=case.id,
                            data={
                                'status': Case.CASE_STATUS_IN_PROGRESS,
                                'assigned_to': extraction_user,
                                'assigned_at': timezone.now()
                            }
                        )
                        
                        self.stdout.write(
                            f"[INFO] Status do caso {case.number} atualizado para 'Em Andamento'"
                        )
                    
            except Exception as e:
                error_count += 1
                error_msg = f"[ERROR] Erro ao iniciar extração {extraction.id}: {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
            
            processed_count += 1

        # Relatório final
        self.stdout.write("\n" + "="*60)
        self.stdout.write("[REPORT] RELATÓRIO FINAL")
        self.stdout.write("="*60)
        self.stdout.write(f"[INFO] Total de extrações encontradas: {total_extractions}")
        if limit:
            self.stdout.write(f"[INFO] Limite aplicado: {limit}")
        self.stdout.write(f"[INFO] Total processadas: {processed_count}")
        self.stdout.write(f"[SUCCESS] Extrações iniciadas com sucesso: {success_count}")
        self.stdout.write(f"[ERROR] Extrações com erro: {error_count}")
        self.stdout.write(f"[INFO] Operação executada por: {assigned_by_user.username}")
        
        if assign_to_user:
            self.stdout.write(f"[INFO] Extrações atribuídas a: {assign_to_user.username}")
        else:
            self.stdout.write(f"[INFO] Extrações atribuídas automaticamente (usuário da extração ou randomizado)")
        
        if errors:
            self.stdout.write("\n[ERROR] ERROS ENCONTRADOS:")
            for error in errors:
                self.stdout.write(f"   {error}")
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n[SUCCESS] {success_count} extrações foram iniciadas com sucesso!")
            )
