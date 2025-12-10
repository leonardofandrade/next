from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from apps.cases.models import Case
from apps.cases.services import CaseService
from apps.configs.services.extractor_service import get_user_extraction_unit_ids


class Command(BaseCommand):
    help = "Busca cases com assigned_to definido e executa a lógica de unassign case"

    def add_arguments(self, parser):
        parser.add_argument(
            '--u',
            type=str,
            help='Login do usuário que executou a operação (unassigned_by) - obrigatório',
            required=True
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Quantidade de cases a processar (padrão: todos os disponíveis)',
            default=None
        )
        parser.add_argument(
            '--assigned_to',
            type=str,
            help='Login do usuário para desatribuir cases específicos (opcional - se não informado, processa todos os cases atribuídos)',
            required=False
        )

    def handle(self, *args, **options):
        username = options['u']
        limit = options['limit']
        assigned_to_username = options.get('assigned_to')

        # Validar usuário unassigned_by
        try:
            unassigned_by_user = User.objects.select_related('profile').get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Usuário com login '{username}' não encontrado")

        # Buscar cases com assigned_to definido
        assigned_cases = Case.objects.filter(assigned_to__isnull=False).select_related('extraction_unit', 'assigned_to')
        
        # Se o usuário é extrator (não superuser), filtrar apenas cases das suas extraction_units
        if not unassigned_by_user.is_superuser:
            if hasattr(unassigned_by_user, 'profile') and unassigned_by_user.profile.is_extractor:
                extraction_unit_ids = get_user_extraction_unit_ids(unassigned_by_user)
                if extraction_unit_ids:
                    assigned_cases = assigned_cases.filter(extraction_unit_id__in=extraction_unit_ids)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Filtrando cases das extraction_units associadas ao usuário '{username}'"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Usuário '{username}' é extrator mas não está associado a nenhuma extraction_unit. "
                            f"Nenhum case será processado."
                        )
                    )
                    assigned_cases = assigned_cases.none()
        
        # Filtrar por usuário específico se informado
        if assigned_to_username:
            try:
                assigned_to_user = User.objects.get(username=assigned_to_username)
                assigned_cases = assigned_cases.filter(assigned_to=assigned_to_user)
                self.stdout.write(
                    self.style.SUCCESS(f"Filtrando cases atribuídos ao usuário: {assigned_to_username}")
                )
            except User.DoesNotExist:
                raise CommandError(f"Usuário com login '{assigned_to_username}' não encontrado")
        
        if not assigned_cases.exists():
            self.stdout.write(
                self.style.WARNING("Nenhum case com assigned_to definido encontrado")
            )
            return

        # Aplicar limite se especificado
        if limit:
            assigned_cases = assigned_cases[:limit]

        total_cases = assigned_cases.count()
        self.stdout.write(
            self.style.SUCCESS(f"Encontrados {total_cases} cases para processar")
        )

        # Processar cases
        case_service = CaseService(user=unassigned_by_user)
        successful_unassignments = 0
        failed_unassignments = 0
        errors = []

        with transaction.atomic():
            for case in assigned_cases:
                try:
                    # Executar unassign case usando o service
                    # O método unassign_from_user só permite desatribuir se o usuário passado for o mesmo atribuído
                    # Como estamos desatribuindo administrativamente, vamos usar update do service
                    if case.assigned_to:
                        updated_case = case_service.update(
                            pk=case.id,
                            data={
                                'assigned_to': None,
                                'assigned_at': None,
                                'assigned_by': None
                            }
                        )
                    else:
                        # Já está desatribuído
                        updated_case = case
                    
                    successful_unassignments += 1
                    extraction_unit_info = f" (Unidade: {case.extraction_unit.name})" if case.extraction_unit else ""
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Case {case.id} desatribuído com sucesso (era de: {case.assigned_to.username}){extraction_unit_info}"
                        )
                    )
                    
                except Exception as e:
                    failed_unassignments += 1
                    error_msg = f"❌ Erro ao desatribuir case {case.id}: {str(e)}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))

        # Relatório final
        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(
                f"📊 RELATÓRIO FINAL:\n"
                f"   • Total de cases processados: {total_cases}\n"
                f"   • Desatribuições bem-sucedidas: {successful_unassignments}\n"
                f"   • Falhas na desatribuição: {failed_unassignments}\n"
                f"   • Operação executada por: {unassigned_by_user.username}"
            )
        )

        if errors:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.ERROR("ERROS ENCONTRADOS:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"   {error}"))

        if failed_unassignments > 0:
            raise CommandError(f"Operação concluída com {failed_unassignments} falhas")
