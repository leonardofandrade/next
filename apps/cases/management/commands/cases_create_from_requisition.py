from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from apps.requisitions.models import ExtractionRequest
from apps.cases.services.case_service import CaseService


class Command(BaseCommand):
    help = "Cria casos (Case) a partir de requisições de extração (ExtractionRequest) com received_at None e marca as requisições como recebidas"

    def add_arguments(self, parser):
        parser.add_argument(
            '--u',
            type=str,
            help='Login do usuário para registrar como created_by (obrigatório)',
            required=True
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limite de requisições para processar (padrão: todas)',
            default=None
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa em modo de simulação sem criar casos reais',
            default=False
        )

    def handle(self, *args, **options):
        username = options['u']
        limit = options['limit']
        dry_run = options['dry_run']

        # Validar usuário created_by
        try:
            created_by_user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Usuário com login '{username}' não encontrado")

        # Buscar requisições com received_at None e sem caso associado
        extraction_requests = ExtractionRequest.objects.filter(
            received_at__isnull=True,
            case__isnull=True  # Apenas requisições que ainda não têm caso
        ).order_by('requested_at')

        total_requests = extraction_requests.count()

        if limit:
            extraction_requests = extraction_requests[:limit]

        if total_requests == 0:
            self.stdout.write(
                self.style.WARNING("Nenhuma requisição de extração encontrada com received_at None")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"Encontradas {total_requests} requisições para processar")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("MODO DRY-RUN: Nenhum caso será criado")
            )

        # Inicializar o serviço de casos com o usuário
        case_service = CaseService(user=created_by_user)

        # Contadores para relatório
        created_cases = []
        errors = []

        # Processar cada requisição
        for i, requisition in enumerate(extraction_requests, 1):
            try:
                self.stdout.write(f"Processando requisição {i}/{total_requests}: ID {requisition.id}")

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f"  [DRY-RUN] Seria criado caso para requisição {requisition.id}")
                    )
                    continue

                # Criar caso usando o serviço e marcar requisição como recebida
                with transaction.atomic():
                    case = case_service.create_case_from_requisition(
                        requisition=requisition,
                        user=created_by_user,
                        mark_request_as_received=True
                    )
                    created_cases.append(case)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ Caso criado: ID {case.id} - "
                        f"Agência: {case.requester_agency_unit.name if case.requester_agency_unit else 'N/A'} - "
                        f"Data: {case.requested_at.strftime('%d/%m/%Y %H:%M')} - "
                        f"Requisição marcada como recebida"
                    )
                )

            except Exception as e:
                error_msg = f"Erro ao processar requisição {requisition.id}: {str(e)}"
                errors.append(error_msg)
                self.stdout.write(
                    self.style.ERROR(f"  ❌ {error_msg}")
                )

        # Relatório final
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("RELATÓRIO DE EXECUÇÃO"))
        self.stdout.write("="*60)

        if dry_run:
            self.stdout.write(f"📊 Modo: DRY-RUN (simulação)")
            self.stdout.write(f"📋 Requisições encontradas: {total_requests}")
            self.stdout.write(f"🔍 Requisições que seriam processadas: {total_requests}")
        else:
            self.stdout.write(f"📊 Modo: EXECUÇÃO REAL")
            self.stdout.write(f"📋 Requisições encontradas: {total_requests}")
            self.stdout.write(f"✅ Casos criados com sucesso: {len(created_cases)}")
            self.stdout.write(f"❌ Erros encontrados: {len(errors)}")

        if errors:
            self.stdout.write("\n🚨 ERROS DETALHADOS:")
            for error in errors:
                self.stdout.write(f"  • {error}")

        if created_cases:
            self.stdout.write(f"\n📝 CASOS CRIADOS:")
            for case in created_cases:
                self.stdout.write(
                    f"  • ID {case.id}: {case.requester_agency_unit.name if case.requester_agency_unit else 'N/A'} - "
                    f"{case.requested_at.strftime('%d/%m/%Y %H:%M')}"
                )

        # Status final
        if dry_run:
            self.stdout.write(f"\n🎯 Execução concluída em modo simulação")
        elif len(errors) == 0:
            self.stdout.write(f"\n🎯 Execução concluída com sucesso!")
        else:
            self.stdout.write(f"\n⚠️  Execução concluída com {len(errors)} erro(s)")
