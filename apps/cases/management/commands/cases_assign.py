import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from apps.cases.models import Case
from apps.cases.services import CaseService
from apps.configs.services.extractor_service import get_available_extractors, get_extractor_assignments_by_unit, check_user_assignment_to_unit


class Command(BaseCommand):
    help = "Busca cases com assigned_to None e executa a lógica de assign case"

    def add_arguments(self, parser):
        parser.add_argument(
            '--u',
            type=str,
            help='Login do usuário que executou a operação (assigned_by) - obrigatório',
            required=True
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Quantidade de cases a processar (padrão: todos os disponíveis)',
            default=None
        )
        parser.add_argument(
            '--assign_to',
            type=str,
            help='Login do usuário para atribuir todos os cases (opcional - se não informado, randomiza entre extratores)',
            required=False
        )

    def handle(self, *args, **options):
        username = options['u']
        limit = options['limit']
        assign_to_username = options.get('assign_to')

        # Validar usuário assigned_by
        try:
            assigned_by_user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Usuário com login '{username}' não encontrado")

        # Buscar cases com assigned_to None
        unassigned_cases = Case.objects.filter(assigned_to__isnull=True)
        
        if not unassigned_cases.exists():
            self.stdout.write(
                self.style.WARNING("Nenhum case com assigned_to None encontrado")
            )
            return

        # Aplicar limite se especificado
        if limit:
            unassigned_cases = unassigned_cases[:limit]

        total_cases = unassigned_cases.count()
        self.stdout.write(
            self.style.SUCCESS(f"Encontrados {total_cases} cases para processar")
        )

        # Processar cases
        case_service = CaseService(user=assigned_by_user)
        successful_assignments = 0
        failed_assignments = 0
        errors = []
        
        # Se um usuário específico foi informado, validar uma vez
        assigned_to_user = None
        if assign_to_username:
            try:
                assigned_to_user = User.objects.select_related('profile').get(username=assign_to_username)
                # Verificar se o usuário é extrator (apenas aviso, não erro)
                if not hasattr(assigned_to_user, 'profile') or not assigned_to_user.profile.is_extractor:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Aviso: Usuário '{assign_to_username}' não é um extrator")
                    )
            except User.DoesNotExist:
                raise CommandError(f"Usuário com login '{assign_to_username}' não encontrado")

        # Cache de extratores por extraction_unit (para otimizar buscas repetidas)
        extractors_by_unit = {}
        
        with transaction.atomic():
            for case in unassigned_cases:
                try:
                    # Determinar usuário para atribuição
                    case_assigned_to_user = assigned_to_user
                    
                    if not case_assigned_to_user:
                        # Se não foi especificado um usuário, buscar extrator da extraction_unit do case
                        if case.extraction_unit:
                            unit_id = case.extraction_unit.id
                            
                            # Buscar extratores da extraction_unit (usar cache se disponível)
                            if unit_id not in extractors_by_unit:
                                assignments = get_extractor_assignments_by_unit(case.extraction_unit)
                                # Filtrar apenas assignments ativos (unassigned_at is null) e usuários ativos
                                active_assignments = [
                                    a.user for a in assignments 
                                    if a.unassigned_at is None and a.user.is_active
                                ]
                                extractors_by_unit[unit_id] = active_assignments
                            
                            available_extractors = extractors_by_unit[unit_id]
                            
                            if not available_extractors:
                                # Se não há extratores associados à extraction_unit, usar fallback
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"⚠️  Nenhum extrator ativo associado à unidade '{case.extraction_unit.name}'. "
                                        f"Usando extratores disponíveis como fallback."
                                    )
                                )
                                # Fallback: buscar todos os extratores disponíveis
                                fallback_extractors = list(get_available_extractors())
                                if not fallback_extractors:
                                    raise Exception(
                                        f"Nenhum extrator disponível para atribuir o case {case.id}. "
                                        f"Unidade: {case.extraction_unit.name}"
                                    )
                                case_assigned_to_user = random.choice(fallback_extractors)
                            else:
                                case_assigned_to_user = random.choice(available_extractors)
                        else:
                            # Case sem extraction_unit - usar fallback geral
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠️  Case {case.id} não possui extraction_unit. "
                                    f"Usando extratores disponíveis como fallback."
                                )
                            )
                            fallback_extractors = list(get_available_extractors())
                            if not fallback_extractors:
                                raise Exception(f"Nenhum extrator disponível para atribuir o case {case.id}")
                            case_assigned_to_user = random.choice(fallback_extractors)
                    else:
                        # Usuário foi especificado - verificar se está associado à extraction_unit do case
                        if case.extraction_unit:
                            if hasattr(case_assigned_to_user, 'profile') and case_assigned_to_user.profile.is_extractor:
                                if not check_user_assignment_to_unit(case_assigned_to_user, case.extraction_unit):
                                    raise Exception(
                                        f"O extrator '{case_assigned_to_user.username}' não está associado à "
                                        f"unidade de extração '{case.extraction_unit.name}' do case {case.id}"
                                    )
                    
                    # Executar assign case
                    updated_case = case_service.assign_to_user(
                        case_pk=case.id,
                        user=case_assigned_to_user
                    )
                    
                    successful_assignments += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Case {case.id} atribuído com sucesso para {case_assigned_to_user.username}"
                        )
                    )
                    
                except Exception as e:
                    failed_assignments += 1
                    error_msg = f"❌ Erro ao atribuir case {case.id}: {str(e)}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))

        # Relatório final
        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(
                f"📊 RELATÓRIO FINAL:\n"
                f"   • Total de cases processados: {total_cases}\n"
                f"   • Atribuições bem-sucedidas: {successful_assignments}\n"
                f"   • Falhas na atribuição: {failed_assignments}\n"
                f"   • Usuário atribuído: {assigned_to_user.username if assigned_to_user else 'Aleatório por case'}\n"
                f"   • Operação executada por: {assigned_by_user.username}"
            )
        )

        if errors:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.ERROR("ERROS ENCONTRADOS:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"   {error}"))

        if failed_assignments > 0:
            raise CommandError(f"Operação concluída com {failed_assignments} falhas")
