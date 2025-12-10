import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from apps.cases.models import Case
from apps.cases.services.case_service import CaseService
from apps.base_tables.models import (
    AgencyUnit, CrimeCategory, EmployeePosition
)
from apps.configs.models import ExtractionUnit

class Command(BaseCommand):
    help = "Cria casos (Case) com dados randômicos para teste"

    def add_arguments(self, parser):
        parser.add_argument(
            '--u',
            type=str,
            help='Login do usuário para registrar como created_by (obrigatório)',
            required=True
        )
        parser.add_argument(
            '--amount',
            type=int,
            help='Quantidade de casos a criar (padrão: 13)',
            default=13
        )
        parser.add_argument(
            '--assigned-to',
            type=str,
            help='Login do usuário para atribuir os casos (opcional)',
            required=False
        )

    def handle(self, *args, **options):
        username = options['u']
        amount = options['amount']
        assign_to = options.get('assign_to')

        # Validar usuário created_by
        try:
            created_by_user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Usuário com login '{username}' não encontrado")

        # Validar usuário assigned_to se fornecido
        assigned_to_user = None
        if assign_to:
            try:
                assigned_to_user = User.objects.get(username=assign_to)
            except User.DoesNotExist:
                raise CommandError(f"Usuário com login '{assign_to}' não encontrado")

        # Buscar EmployeePosition com default_selection=True (primeiro registro ordenado por -default_selection)
        try:
            employee_position = EmployeePosition.objects.filter(default_selection=True).order_by('-default_selection').first()
            if not employee_position:
                # Se não houver nenhum com default_selection=True, pegar o primeiro disponível
                employee_position = EmployeePosition.objects.first()
                if not employee_position:
                    raise CommandError("Nenhum EmployeePosition encontrado no sistema")
        except Exception as e:
            raise CommandError(f"Erro ao buscar EmployeePosition: {str(e)}")

        # Buscar dados necessários para criação randômica
        extraction_units = list(ExtractionUnit.objects.all())
        agency_units = list(AgencyUnit.objects.all())
        crime_categories = list(CrimeCategory.objects.filter(deleted_at__isnull=True))

        if not extraction_units:
            raise CommandError("Nenhuma ExtractionUnit encontrada no sistema")
        if not agency_units:
            raise CommandError("Nenhuma AgencyUnit encontrada no sistema")
        if not crime_categories:
            raise CommandError("Nenhum CrimeCategory encontrado no sistema")

        # Dados para geração randômica
        requester_authority_names = [
            "Dr. João Silva", "Dra. Maria Santos", "Dr. Pedro Oliveira", "Dra. Ana Costa", "Dr. Carlos Ferreira",
            "Dra. Lucia Rodrigues", "Dr. Roberto Alves", "Dra. Fernanda Lima", "Dr. Antonio Pereira", "Dra. Sandra Martins",
            "Dr. Paulo Souza", "Dra. Cristina Nunes", "Dr. Marcos Ribeiro", "Dra. Juliana Dias", "Dr. Rafael Gomes"
        ]

        reply_emails = [
            "joao.silva@policia.gov.br", "maria.santos@policia.gov.br", "pedro.oliveira@policia.gov.br",
            "ana.costa@policia.gov.br", "carlos.ferreira@policia.gov.br", "lucia.rodrigues@policia.gov.br",
            "roberto.alves@policia.gov.br", "fernanda.lima@policia.gov.br", "antonio.pereira@policia.gov.br",
            "sandra.martins@policia.gov.br", "paulo.souza@policia.gov.br", "cristina.nunes@policia.gov.br"
        ]

        # Dados para geração randômica de procedimentos
        request_procedures_samples = [
            "IP 123-456/2025",
            "PJ 1234567-89.2025.8.06.0001",
            "IP 789-012/2025, PJ 9876543-21.2025.8.06.0002",
            "IP 345-678/2025",
            "PJ 1111111-11.2025.8.06.0003, IP 456-789/2025",
            "IP 567-890/2025, PJ 2222222-22.2025.8.06.0004, IP 678-901/2025",
            "PJ 3333333-33.2025.8.06.0005",
            "IP 789-012/2025",
            "PJ 4444444-44.2025.8.06.0006, IP 890-123/2025",
            "IP 901-234/2025, PJ 5555555-55.2025.8.06.0007",
            "IP 012-345/2025",
            "PJ 6666666-66.2025.8.06.0008, IP 123-456/2025, PJ 7777777-77.2025.8.06.0009"
        ]

        # Criar casos usando CaseService
        created_cases = []
        case_service = CaseService(user=created_by_user)
        
        with transaction.atomic():
            for i in range(amount):
                # Gerar dados randômicos
                extraction_unit = random.choice(extraction_units)
                requester_agency_unit = random.choice(agency_units)
                requester_authority_name = random.choice(requester_authority_names)
                crime_category = random.choice(crime_categories)
                reply_email = random.choice(reply_emails)
                request_procedures = random.choice(request_procedures_samples)
                
                # Gerar prioridade randômica
                priority = random.choice([0, 1, 2, 3])
                
                # Gerar data aleatória para requested_at (últimos 30 dias)
                now = timezone.now()
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                requested_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
                
                # Criar o caso usando CaseService
                # NOTA: number e year só são definidos durante complete_registration
                case_data = {
                    'extraction_unit': extraction_unit,
                    'requester_agency_unit': requester_agency_unit,
                    'requester_authority_name': requester_authority_name,
                    'requester_authority_position': employee_position,
                    'requester_reply_email': reply_email,
                    'request_procedures': request_procedures,
                    'status': Case.CASE_STATUS_DRAFT,
                    'priority': priority,
                    'assigned_to': assigned_to_user,
                    'crime_category': crime_category,
                    'requested_at': requested_at,
                }
                
                case = case_service.create(case_data)
                created_cases.append(case)
                
                self.stdout.write(
                    self.style.SUCCESS(f"Caso criado: {case} - {case.requester_authority_name} - Procedimentos: {request_procedures} - Solicitado em: {requested_at.strftime('%d/%m/%Y %H:%M')}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ {len(created_cases)} casos criados com sucesso!\n"
                f"📊 Estatísticas:\n"
                f"   • Status: {Case.CASE_STATUS_DRAFT}\n"
                f"   • EmployeePosition: {employee_position.name}\n"
                f"   • Assigned to: {assigned_to_user.username if assigned_to_user else 'Nenhum'}\n"
                f"   • Created by: {created_by_user.username}"
            )
        )
