from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from django.utils import timezone
from django.contrib.auth.models import User
from apps.cases.models import Case, Extraction
from apps.cases.services.extraction_service import ExtractionService
from apps.configs.models import StorageLocation
from apps.configs.services.extractor_service import check_user_assignment_to_unit
from apps.core.middleware import set_current_user
import random


class Command(BaseCommand):
    help = "Finaliza extrações de forma randomizada, simulando diferentes cenários de finalização"

    def add_arguments(self, parser):
        parser.add_argument(
            '--u',
            type=str,
            dest='username',
            help='Login do usuário que executou a operação (assigned_by) - obrigatório',
            required=True
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
            help='Executa apenas a busca sem finalizar extrações (modo de teste)',
        )
        parser.add_argument(
            '--success-rate',
            type=float,
            default=0.8,
            help='Taxa de sucesso das extrações (0.0 a 1.0). Padrão: 0.8 (80%%)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options.get('limit')
        process_all = options['all']
        username = options['username']
        success_rate = options.get('success_rate')
        
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

        if not 0.0 <= success_rate <= 1.0:
            raise CommandError(
                "Taxa de sucesso deve estar entre 0.0 e 1.0"
            )

        # Validar usuário que executou a operação (assigned_by)
        try:
            assigned_by_user = User.objects.select_related('profile').get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Usuário com login '{username}' não encontrado")
        
        # Definir o usuário atual no thread-local para que os campos do AuditedModel sejam preenchidos
        set_current_user(assigned_by_user)
        
        # Inicializar o service com o usuário
        extraction_service = ExtractionService(user=assigned_by_user)

        # Buscar extrações elegíveis para finalizar
        self.stdout.write("[INFO] Buscando extrações elegíveis para finalizar...")
        
        # Query para buscar extrações com status IN_PROGRESS ou PAUSED
        eligible_extractions = Extraction.objects.filter(
            status__in=[Extraction.STATUS_IN_PROGRESS, Extraction.STATUS_PAUSED]
        ).select_related(
            'case_device',
            'case_device__case',
            'case_device__case__extraction_unit',
            'assigned_to',
            'storage_location'
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
                self.style.WARNING("[DRY-RUN] MODO DRY-RUN: Nenhuma extração será finalizada")
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

        self.stdout.write("[INFO] Iniciando finalização de extrações...")

        for extraction in eligible_extractions:
            try:
                with transaction.atomic():
                    case = extraction.case_device.case
                    
                    # Usar o usuário atribuído à extração ou o usuário que executou a operação
                    # extraction.assigned_to é ExtractorUser, então precisamos pegar o user
                    extraction_user = extraction.assigned_to.user if extraction.assigned_to else assigned_by_user
                    
                    # Validar se o extrator está associado à extraction_unit do case
                    if case.extraction_unit:
                        if hasattr(extraction_user, 'profile') and extraction_user.profile.is_extractor:
                            if not check_user_assignment_to_unit(extraction_user, case.extraction_unit):
                                raise Exception(
                                    f"O extrator '{extraction_user.username}' não está associado à "
                                    f"unidade de extração '{case.extraction_unit.name}' do case {case.id}"
                                )
                    
                    # Determinar se a extração será bem-sucedida baseado na taxa de sucesso
                    is_successful = random.random() < success_rate
                    
                    # Gerar dados aleatórios para a extração
                    extraction_data = self._generate_random_extraction_data(is_successful)
                    
                    # Finalizar a extração usando o serviço
                    # O service já valida se o usuário é extrator e está associado à extraction_unit
                    # Passar todos os dados através de kwargs
                    updated_extraction = extraction_service.complete_extraction(
                        extraction_pk=extraction.id,
                        success=is_successful,
                        notes=extraction_data['notes'],
                        **extraction_data['technical_details']
                    )
                    
                    success_count += 1
                    processed_count += 1
                    
                    result_text = "bem-sucedida" if is_successful else "não bem-sucedida"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[SUCCESS] Extração {updated_extraction.id} finalizada como {result_text} - "
                            f"Caso: {case.number} | "
                            f"Dispositivo: {updated_extraction.case_device.id} | "
                            f"Finalizada por: {extraction_user.username} | "
                            f"Operação executada por: {assigned_by_user.username}"
                        )
                    )
                    
                    # Verificar se o caso deve ser finalizado
                    self._check_and_finalize_case(case, assigned_by_user)
                    
            except Exception as e:
                error_count += 1
                error_msg = f"[ERROR] Erro ao finalizar extração {extraction.id}: {str(e)}"
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
        self.stdout.write(f"[SUCCESS] Extrações finalizadas com sucesso: {success_count}")
        self.stdout.write(f"[ERROR] Extrações com erro: {error_count}")
        self.stdout.write(f"[INFO] Taxa de sucesso configurada: {success_rate:.1%}")
        self.stdout.write(f"[INFO] Operação executada por: {assigned_by_user.username}")
        
        if errors:
            self.stdout.write("\n[ERROR] ERROS ENCONTRADOS:")
            for error in errors:
                self.stdout.write(f"   {error}")
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n[SUCCESS] {success_count} extrações foram finalizadas com sucesso!")
            )

    def _generate_random_extraction_data(self, is_successful):
        """Gera dados aleatórios para finalização da extração"""
        
        # Notas baseadas no resultado
        if is_successful:
            notes_options = [
                "Extração concluída com sucesso. Todos os dados foram extraídos.",
                "Processo finalizado sem problemas. Dados salvos no local de armazenamento.",
                "Extração bem-sucedida. Arquivos organizados e prontos para análise.",
                "Finalização completa. Dados extraídos e catalogados adequadamente.",
                "Extração finalizada com êxito. Relatório técnico anexado."
            ]
        else:
            notes_options = [
                "Extração falhou devido a problemas técnicos no dispositivo.",
                "Não foi possível extrair dados devido a danos físicos no dispositivo.",
                "Falha na extração por problemas de compatibilidade de software.",
                "Extração interrompida devido a erro no sistema de arquivos.",
                "Processo finalizado sem sucesso. Dispositivo apresentou problemas."
            ]
        
        # Detalhes técnicos aleatórios
        technical_details = {
            'logical_extraction': random.choice([True, False]),
            'physical_extraction': random.choice([True, False]),
            'full_file_system_extraction': random.choice([True, False]),
            'cloud_extraction': random.choice([True, False]),
            'cellebrite_premium': random.choice([True, False]),
            'cellebrite_premium_support': random.choice([True, False]),
            'extraction_size': random.randint(1, 500) if is_successful else random.randint(0, 50),
        }
        
        # Adicionar notas específicas para cada tipo de extração
        if technical_details['logical_extraction']:
            technical_details['logical_extraction_notes'] = "Extração lógica realizada com sucesso."
        
        if technical_details['physical_extraction']:
            technical_details['physical_extraction_notes'] = "Extração física concluída."
        
        if technical_details['full_file_system_extraction']:
            technical_details['full_file_system_extraction_notes'] = "Sistema de arquivos completo extraído."
        
        if technical_details['cloud_extraction']:
            technical_details['cloud_extraction_notes'] = "Dados em nuvem extraídos."
        
        if technical_details['cellebrite_premium']:
            technical_details['cellebrite_premium_notes'] = "Cellebrite Premium utilizado."
        
        if technical_details['cellebrite_premium_support']:
            technical_details['cellebrite_premium_support_notes'] = "Suporte Cellebrite Premium ativado."
        
        # Atribuir local de armazenamento aleatório se disponível
        storage_locations = StorageLocation.objects.filter(deleted_at__isnull=True)
        if storage_locations.exists():
            technical_details['storage_location'] = random.choice(storage_locations)
        
        return {
            'notes': random.choice(notes_options),
            'technical_details': technical_details
        }

    def _check_and_finalize_case(self, case, user):
        """Verifica se o caso deve ser finalizado após finalizar todas as extrações"""
        try:
            from apps.cases.services.case_service import CaseService
            
            # Verificar se todas as extrações do caso foram finalizadas
            case_extractions = Extraction.objects.filter(
                case_device__case=case
            )
            
            total_extractions = case_extractions.count()
            completed_extractions = case_extractions.filter(
                status=Extraction.STATUS_COMPLETED
            ).count()
            
            # Se todas as extrações foram finalizadas, finalizar o caso
            if total_extractions > 0 and completed_extractions == total_extractions:
                if case.status in [Case.CASE_STATUS_IN_PROGRESS, Case.CASE_STATUS_PAUSED]:
                    case_service = CaseService(user=user)
                    case_service.update(
                        pk=case.id,
                        data={
                            'status': Case.CASE_STATUS_COMPLETED,
                            'finished_at': timezone.now(),
                            'finalization_notes': f"Caso finalizado automaticamente após conclusão de todas as {total_extractions} extrações."
                        }
                    )
                    
                    self.stdout.write(
                        f"[INFO] Caso {case.number} finalizado automaticamente (todas as extrações concluídas)"
                    )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"[WARNING] Erro ao verificar finalização do caso {case.number}: {str(e)}")
            )
