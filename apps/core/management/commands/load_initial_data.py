import json
import base64
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

from apps.base_tables.models import (
    Organization, Agency, Department, AgencyUnit,
    EmployeePosition, CrimeCategory, DeviceCategory,
    DeviceBrand, DeviceModel, ProcedureCategory
)
from apps.users.models import UserProfile
from apps.core.models import (
    ExtractionAgency, ExtractionUnit, ExtractorUser,
    GeneralSettings, EmailSettings, ReportsSettings
)


class Command(BaseCommand):
    help = 'Carrega dados iniciais dos arquivos JSON em initial_data/'

    def __init__(self):
        super().__init__()
        self.base_path = Path('initial_data')

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Nome específico do arquivo JSON para carregar (sem caminho)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa os dados existentes antes de carregar',
        )

    def handle(self, *args, **options):
        file_name = options.get('file')
        clear_data = options.get('clear', False)

        if clear_data:
            self.stdout.write(self.style.WARNING('Limpando dados existentes...'))
            self.clear_existing_data()

        try:
            with transaction.atomic():
                if file_name:
                    # Carrega apenas o arquivo especificado
                    file_path = self.base_path / file_name
                    if not file_path.exists():
                        self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {file_path}'))
                        return
                    self.load_file(file_path)
                else:
                    # Carrega todos os arquivos na ordem correta
                    self.load_all_files()

                self.stdout.write(self.style.SUCCESS('Dados carregados com sucesso!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao carregar dados: {str(e)}'))
            raise

    def clear_existing_data(self):
        """Limpa dados existentes (cuidado em produção!)"""
        # A ordem importa devido às foreign keys
        ReportsSettings.objects.all().delete()
        EmailSettings.objects.all().delete()
        GeneralSettings.objects.all().delete()
        ExtractorUser.objects.all().delete()
        ExtractionUnit.objects.all().delete()
        ExtractionAgency.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        DeviceModel.objects.all().delete()
        DeviceBrand.objects.all().delete()
        DeviceCategory.objects.all().delete()
        CrimeCategory.objects.all().delete()
        ProcedureCategory.objects.all().delete()
        EmployeePosition.objects.all().delete()
        AgencyUnit.objects.all().delete()
        Department.objects.all().delete()
        Agency.objects.all().delete()
        Organization.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Dados existentes removidos.'))

    def load_all_files(self):
        """Carrega todos os arquivos JSON na ordem correta"""
        files = [
            '01_employee_positions.json',
            '02_organizations.json',
            '03_pcce_agency_units.json',
            '04_users.json',
            '05_extraction_agency.json',
            '06_crime_category.json',
            '07_device_category.json',
            '08_device_brands_models.json',
            '09_procedure_category.json',
            '10_extraction_agency_and_settings.json',
        ]

        for file_name in files:
            file_path = self.base_path / file_name
            if file_path.exists():
                self.stdout.write(f'Carregando {file_name}...')
                self.load_file(file_path)
            else:
                self.stdout.write(self.style.WARNING(f'Arquivo não encontrado: {file_path}'))

    def load_file(self, file_path: Path):
        """Carrega um arquivo JSON específico"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        file_name = file_path.name

        if file_name == '01_employee_positions.json':
            self.load_employee_positions(data)
        elif file_name == '02_organizations.json':
            self.load_organizations(data)
        elif file_name == '03_pcce_agency_units.json':
            self.load_pcce_agency_units(data)
        elif file_name == '04_users.json':
            self.load_users(data)
        elif file_name == '05_extraction_agency.json':
            self.load_extraction_agency(data)
        elif file_name == '06_crime_category.json':
            self.load_crime_categories(data)
        elif file_name == '07_device_category.json':
            self.load_device_categories(data)
        elif file_name == '08_device_brands_models.json':
            self.load_device_brands_models(data)
        elif file_name == '09_procedure_category.json':
            self.load_procedure_categories(data)
        elif file_name == '10_extraction_agency_and_settings.json':
            self.load_extraction_agency_and_settings(data)

    def load_employee_positions(self, data):
        """Carrega cargos de funcionários"""
        count = 0
        for item in data:
            _, created = EmployeePosition.objects.get_or_create(
                acronym=item['acronym'],
                defaults={
                    'name': item['name'],
                    'default_selection': item.get('default_selection', False)
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'  {count} cargos criados'))

    def load_organizations(self, data):
        """Carrega organizações, agências e unidades"""
        org_count = 0
        agency_count = 0
        unit_count = 0

        for org_data in data['organizations']:
            org, org_created = Organization.objects.get_or_create(
                acronym=org_data['acronym'],
                defaults={'name': org_data['name']}
            )
            if org_created:
                org_count += 1

            for agency_data in org_data['agencies']:
                agency, agency_created = Agency.objects.get_or_create(
                    organization=org,
                    acronym=agency_data['acronym'],
                    defaults={
                        'name': agency_data['name'],
                        'description': agency_data.get('description', '')
                    }
                )
                if agency_created:
                    agency_count += 1

                for unit_data in agency_data.get('agency_units', []):
                    unit, unit_created = AgencyUnit.objects.get_or_create(
                        agency=agency,
                        acronym=unit_data['acronym'],
                        defaults={
                            'name': unit_data['name'],
                            'phone_number': unit_data.get('phone', ''),
                            'primary_email': unit_data.get('email', ''),
                            'address_line_1': unit_data.get('address_line1', ''),
                            'address_number': unit_data.get('address_number', ''),
                            'address_line_2': unit_data.get('address_line2', ''),
                            'neighborhood': unit_data.get('neighborhood', ''),
                            'city': unit_data.get('city_name', ''),
                            'address_postal_code': unit_data.get('postal_code', ''),
                        }
                    )
                    if unit_created:
                        unit_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  {org_count} organizações, {agency_count} agências, {unit_count} unidades criadas'
        ))

    def load_pcce_agency_units(self, data):
        """Carrega departamentos e unidades da PCCE"""
        dept_count = 0
        unit_count = 0

        # Busca a agência PCCE
        try:
            pcce_agency = Agency.objects.get(acronym='PCCE')
        except Agency.DoesNotExist:
            self.stdout.write(self.style.ERROR('  Agência PCCE não encontrada. Execute 02_organizations.json primeiro.'))
            return

        # Carrega departamentos
        for dept_data in data.get('departments', []):
            dept, created = Department.objects.get_or_create(
                agency=pcce_agency,
                acronym=dept_data['acronym'],
                defaults={
                    'name': dept_data['name'],
                    'description': dept_data.get('description', '')
                }
            )
            if created:
                dept_count += 1

        # Carrega unidades da PCCE
        for unit_data in data.get('agency_units', []):
            # Busca o departamento se especificado
            department = None
            if 'department' in unit_data:
                try:
                    department = Department.objects.get(
                        agency=pcce_agency,
                        name=unit_data['department']
                    )
                except Department.DoesNotExist:
                    pass

            unit, created = AgencyUnit.objects.get_or_create(
                agency=pcce_agency,
                acronym=unit_data['acronym'],
                defaults={
                    'name': unit_data['name'],
                    'phone_number': self._format_phone(unit_data.get('phone_number', '')),
                    'primary_email': unit_data.get('email', ''),
                    'address_line_1': unit_data.get('address_line_1', ''),
                    'address_number': unit_data.get('address_number', ''),
                    'address_line_2': unit_data.get('address_line_2', ''),
                    'neighborhood': unit_data.get('neighborhood', ''),
                    'city': unit_data.get('city', ''),
                    'address_postal_code': unit_data.get('postal_code', ''),
                }
            )
            if created:
                unit_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  {dept_count} departamentos, {unit_count} unidades da PCCE criadas'
        ))

    def _format_phone(self, phone):
        """Formata número de telefone - aceita string ou lista"""
        if isinstance(phone, list):
            return phone[0] if phone else ''
        return phone or ''

    def load_users(self, data):
        """Carrega usuários"""
        count = 0
        for user_data in data:
            # Busca a organização, agência e unidade
            try:
                organization = Organization.objects.get(acronym=user_data['organization'])
                agency = Agency.objects.get(
                    organization=organization,
                    acronym=user_data['agency']
                )
                agency_unit = AgencyUnit.objects.get(
                    agency=agency,
                    acronym=user_data['agency_unit']
                )
                employee_position = EmployeePosition.objects.get(
                    name=user_data['employee_position']
                )
            except (Organization.DoesNotExist, Agency.DoesNotExist, 
                    AgencyUnit.DoesNotExist, EmployeePosition.DoesNotExist) as e:
                self.stdout.write(self.style.WARNING(
                    f'  Pulando usuário {user_data["employee_id"]}: {str(e)}'
                ))
                continue

            # Cria ou atualiza o usuário Django
            user, user_created = User.objects.get_or_create(
                username=user_data['employee_id'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': user_data['email'],
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False),
                }
            )

            if user_created:
                # Define senha padrão para testes
                user.set_password('123qwe')
                user.save()

            # Cria ou atualiza o perfil do usuário
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'agency_unit': agency_unit,
                    'employee_position': employee_position,
                    'employee_id': user_data['employee_id'],
                    'phone_number': user_data.get('phone_number', ''),
                    'mobile_number': user_data.get('mobile_number', ''),
                }
            )

            if user_created or profile_created:
                count += 1

            # Se for extrator, cria o registro ExtractorUser
            if user_data.get('is_extractor', False):
                # Busca a agência de extração (assume que já foi criada)
                try:
                    extraction_agency = ExtractionAgency.objects.first()
                    if extraction_agency:
                        ExtractorUser.objects.get_or_create(
                            user=user,
                            extraction_agency=extraction_agency,
                        )
                except ExtractionAgency.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  Agência de extração não encontrada para usuário {user.username}'
                    ))

        self.stdout.write(self.style.SUCCESS(f'  {count} usuários criados'))

    def load_extraction_agency(self, data):
        """Carrega agência de extração e unidades de extração"""
        agency_data = data['extraction_agency']

        # Cria agência de extração
        extraction_agency, created = ExtractionAgency.objects.get_or_create(
            acronym=agency_data['acronym'],
            defaults={'name': agency_data['name']}
        )
        
        # Atualiza campos adicionais se não foi criado agora
        if not created:
            extraction_agency.name = agency_data['name']
            extraction_agency.incharge_name = agency_data.get('incharge_name')
            extraction_agency.incharge_position = agency_data.get('incharge_position')
            extraction_agency.save()
        
        # Carrega logo se existir
        if agency_data.get('main_logo_base64'):
            try:
                logo_bytes = base64.b64decode(agency_data['main_logo_base64'])
                extraction_agency.main_logo = logo_bytes
                extraction_agency.save()
                self.stdout.write(self.style.SUCCESS('  Logo da agência carregado'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Erro ao carregar logo: {str(e)}'))
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Agência de extração criada: {extraction_agency}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  Agência de extração atualizada: {extraction_agency}'))

        # Carrega unidades de extração
        unit_count = 0
        for unit_data in data.get('extraction_units', []):
            unit, unit_created = ExtractionUnit.objects.get_or_create(
                agency=extraction_agency,
                acronym=unit_data['acronym'],
                defaults={
                    'name': unit_data['name'],
                    'primary_phone': unit_data.get('primary_phone', ''),
                    'secondary_phone': unit_data.get('secondary_phone', ''),
                    'primary_email': unit_data.get('primary_email', ''),
                    'secondary_email': unit_data.get('secondary_email', ''),
                    'address_line1': unit_data.get('address_line1', ''),
                    'address_number': unit_data.get('address_number', ''),
                    'address_line2': unit_data.get('address_line2', ''),
                    'neighborhood': unit_data.get('neighborhood', ''),
                    'city_name': unit_data.get('city_name', ''),
                    'postal_code': unit_data.get('postal_code', ''),
                    'state_name': unit_data.get('state_name', 'CE'),
                    'country_name': unit_data.get('country_name', 'Brasil'),
                    'reply_email_template': unit_data.get('reply_email_template', ''),
                    'reply_email_subject': unit_data.get('reply_email_subject', ''),
                    'incharge_name': unit_data.get('incharge_name', ''),
                    'incharge_position': unit_data.get('incharge_position', ''),
                }
            )
            if unit_created:
                unit_count += 1

        self.stdout.write(self.style.SUCCESS(f'  {unit_count} unidades de extração criadas'))

    def load_crime_categories(self, data):
        """Carrega categorias de crime"""
        count = 0
        for item in data:
            _, created = CrimeCategory.objects.get_or_create(
                acronym=item['acronym'],
                defaults={
                    'name': item['name'],
                    'default_selection': item.get('default_selection', False)
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'  {count} categorias de crime criadas'))

    def load_device_categories(self, data):
        """Carrega categorias de dispositivos"""
        count = 0
        for item in data['device_types']:
            _, created = DeviceCategory.objects.get_or_create(
                name=item['name'],
                defaults={
                    'acronym': item['name'][:10].upper(),
                    'description': item.get('description', ''),
                    'default_selection': item.get('default_selection', False)
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'  {count} categorias de dispositivo criadas'))

    def load_device_brands_models(self, data):
        """Carrega marcas e modelos de dispositivos"""
        brand_count = 0
        model_count = 0

        for brand_data in data['brands']:
            brand, brand_created = DeviceBrand.objects.get_or_create(
                name=brand_data['name'],
                defaults={
                    'acronym': brand_data['name'][:10].upper(),
                    'description': brand_data.get('description', '')
                }
            )
            if brand_created:
                brand_count += 1

            for model_data in brand_data.get('models', []):
                model, model_created = DeviceModel.objects.get_or_create(
                    brand=brand,
                    name=model_data['name'],
                    defaults={
                        'commercial_name': model_data.get('commercial_name', ''),
                        'code': model_data.get('code', ''),
                        'description': model_data.get('description', '')
                    }
                )
                if model_created:
                    model_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  {brand_count} marcas, {model_count} modelos de dispositivo criados'
        ))

    def load_procedure_categories(self, data):
        """Carrega categorias de procedimento"""
        count = 0
        for item in data:
            _, created = ProcedureCategory.objects.get_or_create(
                acronym=item['acronym'],
                defaults={
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'default_selection': item.get('default_selection', False)
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'  {count} categorias de procedimento criadas'))

    def load_extraction_agency_and_settings(self, data):
        """Carrega ExtractionAgency e Settings do arquivo exportado"""
        # Carrega ExtractionAgency
        if data.get('extraction_agency'):
            agency_data = data['extraction_agency']
            
            # Busca ou cria a agência
            extraction_agency, created = ExtractionAgency.objects.get_or_create(
                acronym=agency_data['acronym'],
                defaults={'name': agency_data['name']}
            )
            
            # Atualiza campos
            extraction_agency.name = agency_data['name']
            extraction_agency.incharge_name = agency_data.get('incharge_name')
            extraction_agency.incharge_position = agency_data.get('incharge_position')
            
            # Carrega logo se existir
            if agency_data.get('main_logo_base64'):
                try:
                    logo_bytes = base64.b64decode(agency_data['main_logo_base64'])
                    extraction_agency.main_logo = logo_bytes
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Erro ao carregar logo da agência: {str(e)}'))
            
            extraction_agency.save()
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Agência de extração criada: {extraction_agency}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  Agência de extração atualizada: {extraction_agency}'))
        else:
            self.stdout.write(self.style.WARNING('  Nenhuma ExtractionAgency encontrada no arquivo'))
            return

        # Carrega Settings
        settings_data = data.get('settings', {})
        
        # GeneralSettings
        if settings_data.get('general'):
            self.load_general_settings(settings_data['general'], extraction_agency)
        else:
            self.stdout.write(self.style.WARNING('  Nenhum GeneralSettings encontrado no arquivo'))
        
        # EmailSettings
        if settings_data.get('email'):
            self.load_email_settings(settings_data['email'], extraction_agency)
        else:
            self.stdout.write(self.style.WARNING('  Nenhum EmailSettings encontrado no arquivo'))
        
        # ReportsSettings
        if settings_data.get('reports'):
            self.load_reports_settings(settings_data['reports'], extraction_agency)
        else:
            self.stdout.write(self.style.WARNING('  Nenhum ReportsSettings encontrado no arquivo'))

    def load_general_settings(self, data, extraction_agency):
        """Carrega GeneralSettings"""
        settings, created = GeneralSettings.objects.get_or_create(
            extraction_agency=extraction_agency,
            defaults={
                'system_name': data.get('system_name'),
                'system_version': data.get('system_version'),
                'system_description': data.get('system_description'),
                'primary_color': data.get('primary_color'),
                'secondary_color': data.get('secondary_color'),
                'maintenance_mode': data.get('maintenance_mode', False),
                'maintenance_message': data.get('maintenance_message'),
                'backup_enabled': data.get('backup_enabled', False),
                'backup_frequency': data.get('backup_frequency', 'daily'),
            }
        )
        
        # Atualiza se já existia
        if not created:
            settings.system_name = data.get('system_name')
            settings.system_version = data.get('system_version')
            settings.system_description = data.get('system_description')
            settings.primary_color = data.get('primary_color')
            settings.secondary_color = data.get('secondary_color')
            settings.maintenance_mode = data.get('maintenance_mode', False)
            settings.maintenance_message = data.get('maintenance_message')
            settings.backup_enabled = data.get('backup_enabled', False)
            settings.backup_frequency = data.get('backup_frequency', 'daily')
            settings.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('  GeneralSettings criado'))
        else:
            self.stdout.write(self.style.SUCCESS('  GeneralSettings atualizado'))

    def load_email_settings(self, data, extraction_agency):
        """Carrega EmailSettings"""
        settings, created = EmailSettings.objects.get_or_create(
            extraction_agency=extraction_agency,
            defaults={
                'email_host': data.get('email_host', 'localhost'),
                'email_port': data.get('email_port', 587),
                'email_use_tls': data.get('email_use_tls', True),
                'email_use_ssl': data.get('email_use_ssl', False),
                'email_host_user': data.get('email_host_user', ''),
                'email_host_password': data.get('email_host_password', ''),
                'email_from_name': data.get('email_from_name', 'Sistema'),
            }
        )
        
        # Atualiza se já existia
        if not created:
            settings.email_host = data.get('email_host', 'localhost')
            settings.email_port = data.get('email_port', 587)
            settings.email_use_tls = data.get('email_use_tls', True)
            settings.email_use_ssl = data.get('email_use_ssl', False)
            settings.email_host_user = data.get('email_host_user', '')
            settings.email_host_password = data.get('email_host_password', '')
            settings.email_from_name = data.get('email_from_name', 'Sistema')
            settings.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('  EmailSettings criado'))
        else:
            self.stdout.write(self.style.SUCCESS('  EmailSettings atualizado'))

    def load_reports_settings(self, data, extraction_agency):
        """Carrega ReportsSettings"""
        settings, created = ReportsSettings.objects.get_or_create(
            extraction_agency=extraction_agency,
            defaults={
                'reports_enabled': data.get('reports_enabled', True),
                'distribution_report_notes': data.get('distribution_report_notes'),
                'report_cover_header_line_1': data.get('report_cover_header_line_1'),
                'report_cover_header_line_2': data.get('report_cover_header_line_2'),
                'report_cover_header_line_3': data.get('report_cover_header_line_3'),
                'report_cover_footer_line_1': data.get('report_cover_footer_line_1'),
                'report_cover_footer_line_2': data.get('report_cover_footer_line_2'),
            }
        )
        
        # Atualiza se já existia
        if not created:
            settings.reports_enabled = data.get('reports_enabled', True)
            settings.distribution_report_notes = data.get('distribution_report_notes')
            settings.report_cover_header_line_1 = data.get('report_cover_header_line_1')
            settings.report_cover_header_line_2 = data.get('report_cover_header_line_2')
            settings.report_cover_header_line_3 = data.get('report_cover_header_line_3')
            settings.report_cover_footer_line_1 = data.get('report_cover_footer_line_1')
            settings.report_cover_footer_line_2 = data.get('report_cover_footer_line_2')
        
        # Carrega logos se existirem
        if data.get('default_report_header_logo_base64'):
            try:
                logo_bytes = base64.b64decode(data['default_report_header_logo_base64'])
                settings.default_report_header_logo = logo_bytes
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Erro ao carregar logo padrão: {str(e)}'))
        
        if data.get('secondary_report_header_logo_base64'):
            try:
                logo_bytes = base64.b64decode(data['secondary_report_header_logo_base64'])
                settings.secondary_report_header_logo = logo_bytes
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Erro ao carregar logo secundário: {str(e)}'))
        
        settings.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ReportsSettings criado'))
        else:
            self.stdout.write(self.style.SUCCESS('  ReportsSettings atualizado'))
