"""
Management command para gerar solicitações de extração para testes
"""
import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

from apps.requisitions.services import ExtractionRequestService
from apps.requisitions.models import ExtractionRequest
from apps.core.services.base import ValidationServiceException
from apps.base_tables.models import AgencyUnit, EmployeePosition, CrimeCategory, ProcedureCategory
from apps.core.models import ExtractionUnit


class Command(BaseCommand):
    help = 'Gera solicitações de extração para testes usando Faker'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Login/username do usuário que criará as solicitações'
        )
        parser.add_argument(
            'quantity',
            type=int,
            help='Quantidade de solicitações a serem geradas'
        )
        parser.add_argument(
            '--max-devices',
            type=int,
            default=1,
            help='Quantidade máxima de dispositivos por solicitação (default: 1)'
        )

    def handle(self, *args, **options):
        username = options['username']
        quantity = options['quantity']
        max_devices = options['max_devices']

        # Valida quantidade
        if quantity < 1:
            raise CommandError('A quantidade deve ser maior que zero.')
        
        if max_devices < 1:
            raise CommandError('A quantidade máxima de dispositivos deve ser maior que zero.')

        # Busca o usuário
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Usuário "{username}" não encontrado.')

        # Verifica se existem dados necessários
        agency_units = list(AgencyUnit.objects.filter(deleted_at__isnull=True))
        if not agency_units:
            raise CommandError('Não há unidades de agência cadastradas.')

        extraction_units = list(ExtractionUnit.objects.filter(deleted_at__isnull=True))
        if not extraction_units:
            raise CommandError('Não há unidades de extração cadastradas.')

        employee_positions = list(EmployeePosition.objects.filter(deleted_at__isnull=True))
        if not employee_positions:
            raise CommandError('Não há cargos cadastrados.')

        crime_categories = list(CrimeCategory.objects.filter(deleted_at__isnull=True))
        if not crime_categories:
            raise CommandError('Não há categorias de crime cadastradas.')

        procedure_categories = list(ProcedureCategory.objects.filter(deleted_at__isnull=True))
        if not procedure_categories:
            self.stdout.write(
                self.style.WARNING('Aviso: Não há categorias de procedimento cadastradas. '
                                 'Usando valores padrão.')
            )
            procedure_categories = None

        # Inicializa Faker
        fake = Faker('pt_BR')
        
        # Inicializa o service
        request_service = ExtractionRequestService(user=user)

        self.stdout.write(f'Gerando {quantity} solicitações de extração...')

        created_count = 0
        for i in range(quantity):
            try:
                # Seleciona dados aleatórios
                requester_agency_unit = random.choice(agency_units)
                extraction_unit = random.choice(extraction_units)
                authority_position = random.choice(employee_positions)
                crime_category = random.choice(crime_categories)
                
                # Gera número de procedimentos (1 a 5 procedimentos separados por vírgula)
                num_procedures = random.randint(1, 5)
                procedures = []
                
                for _ in range(num_procedures):
                    if procedure_categories:
                        procedure_cat = random.choice(procedure_categories)
                        proc_num = f"{procedure_cat.acronym} {random.randint(1, 9999):04d}/{timezone.now().year}"
                    else:
                        # Valores padrão se não houver categorias de procedimento
                        proc_types = ['IP', 'PJ', 'TCO', 'APF', 'BO', 'DJ', 'TA', 'AAA']
                        proc_num = f"{random.choice(proc_types)} {random.randint(1, 9999):04d}/{timezone.now().year}"
                    procedures.append(proc_num)
                
                procedure_number = ', '.join(procedures)

                # Gera nome de autoridade
                authority_name = fake.name()

                # Gera email
                requester_email = fake.email()

                # Gera quantidade de dispositivos (1 até max_devices)
                device_amount = random.randint(1, max_devices)

                # Gera informações adicionais (50% de chance de ter)
                additional_info = fake.text(max_nb_chars=200) if random.random() > 0.5 else None

                # Gera data de solicitação aleatória (entre hoje e 4 anos atrás)
                now = timezone.now()
                days_ago = random.randint(0, 365 * 4)  # 4 anos = ~1460 dias
                requested_at = now - timezone.timedelta(days=days_ago, 
                                                       hours=random.randint(0, 23),
                                                       minutes=random.randint(0, 59))

                # Prepara dados para criação via service
                request_data = {
                    'requester_agency_unit': requester_agency_unit,
                    'requested_at': requested_at,
                    'requested_device_amount': device_amount,
                    'extraction_unit': extraction_unit,
                    'requester_reply_email': requester_email,
                    'requester_authority_name': authority_name,
                    'requester_authority_position': authority_position,
                    'request_procedures': procedure_number,
                    'crime_category': crime_category,
                    'status': ExtractionRequest.REQUEST_STATUS_ASSIGNED,
                }
                
                # Adiciona campos opcionais apenas se não forem None
                if additional_info:
                    request_data['additional_info'] = additional_info

                # Usa o service para criar a solicitação
                extraction_request = request_service.create(request_data)

                created_count += 1
                
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'  {i + 1}/{quantity} solicitações criadas...')

            except ValidationServiceException as e:
                self.stdout.write(
                    self.style.ERROR(f'Erro de validação ao criar solicitação #{i + 1}: {str(e)}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erro ao criar solicitação #{i + 1}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ {created_count} solicitações de extração criadas com sucesso!')
        )
        
        if created_count < quantity:
            self.stdout.write(
                self.style.WARNING(f'Aviso: {quantity - created_count} solicitações falharam.')
            )
