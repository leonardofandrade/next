import json
import base64
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from apps.core.models import (
    ExtractionAgency,
    GeneralSettings,
    EmailSettings,
    ReportsSettings
)


class Command(BaseCommand):
    help = 'Exporta dados de ExtractionAgency e Settings para JSON em initial_data/'

    def __init__(self):
        super().__init__()
        self.base_path = Path('initial_data')

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Nome do arquivo de saída (sem caminho). Padrão: extraction_agency_and_settings.json',
            default='extraction_agency_and_settings.json',
        )

    def handle(self, *args, **options):
        output_file = options.get('output')
        output_path = self.base_path / output_file

        # Garante que o diretório existe
        self.base_path.mkdir(exist_ok=True)

        try:
            data = self.export_data()
            
            # Salva o JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
            
            self.stdout.write(
                self.style.SUCCESS(f'Dados exportados com sucesso para: {output_path}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao exportar dados: {str(e)}')
            )
            raise

    def export_data(self):
        """Exporta todos os dados necessários"""
        data = {}

        # Exporta ExtractionAgency
        extraction_agencies = ExtractionAgency.objects.filter(deleted_at__isnull=True)
        if extraction_agencies.exists():
            # Assumindo que há apenas uma agência (conforme comentário no modelo)
            agency = extraction_agencies.first()
            data['extraction_agency'] = self.serialize_extraction_agency(agency)
        else:
            data['extraction_agency'] = None
            self.stdout.write(self.style.WARNING('Nenhuma ExtractionAgency encontrada'))

        # Exporta Settings
        data['settings'] = {}
        
        # GeneralSettings
        general_settings = GeneralSettings.objects.filter(deleted_at__isnull=True).first()
        if general_settings:
            data['settings']['general'] = self.serialize_general_settings(general_settings)
        else:
            data['settings']['general'] = None
            self.stdout.write(self.style.WARNING('Nenhum GeneralSettings encontrado'))

        # EmailSettings
        email_settings = EmailSettings.objects.filter(deleted_at__isnull=True).first()
        if email_settings:
            data['settings']['email'] = self.serialize_email_settings(email_settings)
        else:
            data['settings']['email'] = None
            self.stdout.write(self.style.WARNING('Nenhum EmailSettings encontrado'))

        # ReportsSettings
        reports_settings = ReportsSettings.objects.filter(deleted_at__isnull=True).first()
        if reports_settings:
            data['settings']['reports'] = self.serialize_reports_settings(reports_settings)
        else:
            data['settings']['reports'] = None
            self.stdout.write(self.style.WARNING('Nenhum ReportsSettings encontrado'))

        return data

    def serialize_extraction_agency(self, agency):
        """Serializa ExtractionAgency"""
        data = {
            'acronym': agency.acronym,
            'name': agency.name,
            'incharge_name': agency.incharge_name,
            'incharge_position': agency.incharge_position,
        }

        # Converte logo para base64 se existir
        if agency.main_logo:
            try:
                data['main_logo_base64'] = base64.b64encode(agency.main_logo).decode('utf-8')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Erro ao converter logo da agência: {str(e)}')
                )
                data['main_logo_base64'] = None
        else:
            data['main_logo_base64'] = None

        return data

    def serialize_general_settings(self, settings):
        """Serializa GeneralSettings"""
        data = {
            'system_name': settings.system_name,
            'system_version': settings.system_version,
            'system_description': settings.system_description,
            'primary_color': settings.primary_color,
            'secondary_color': settings.secondary_color,
            'maintenance_mode': settings.maintenance_mode,
            'maintenance_message': settings.maintenance_message,
            'backup_enabled': settings.backup_enabled,
            'backup_frequency': settings.backup_frequency,
        }

        # Referência à agência pelo acronym
        if settings.extraction_agency:
            data['extraction_agency_acronym'] = settings.extraction_agency.acronym
        else:
            data['extraction_agency_acronym'] = None

        return data

    def serialize_email_settings(self, settings):
        """Serializa EmailSettings"""
        data = {
            'email_host': settings.email_host,
            'email_port': settings.email_port,
            'email_use_tls': settings.email_use_tls,
            'email_use_ssl': settings.email_use_ssl,
            'email_host_user': settings.email_host_user,
            'email_host_password': settings.email_host_password,
            'email_from_name': settings.email_from_name,
        }

        # Referência à agência pelo acronym
        if settings.extraction_agency:
            data['extraction_agency_acronym'] = settings.extraction_agency.acronym
        else:
            data['extraction_agency_acronym'] = None

        return data

    def serialize_reports_settings(self, settings):
        """Serializa ReportsSettings"""
        data = {
            'reports_enabled': settings.reports_enabled,
            'distribution_report_notes': settings.distribution_report_notes,
            'report_cover_header_line_1': settings.report_cover_header_line_1,
            'report_cover_header_line_2': settings.report_cover_header_line_2,
            'report_cover_header_line_3': settings.report_cover_header_line_3,
            'report_cover_footer_line_1': settings.report_cover_footer_line_1,
            'report_cover_footer_line_2': settings.report_cover_footer_line_2,
        }

        # Converte logos para base64 se existirem
        if settings.default_report_header_logo:
            try:
                data['default_report_header_logo_base64'] = base64.b64encode(
                    settings.default_report_header_logo
                ).decode('utf-8')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Erro ao converter logo padrão: {str(e)}')
                )
                data['default_report_header_logo_base64'] = None
        else:
            data['default_report_header_logo_base64'] = None

        if settings.secondary_report_header_logo:
            try:
                data['secondary_report_header_logo_base64'] = base64.b64encode(
                    settings.secondary_report_header_logo
                ).decode('utf-8')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Erro ao converter logo secundário: {str(e)}')
                )
                data['secondary_report_header_logo_base64'] = None
        else:
            data['secondary_report_header_logo_base64'] = None

        # Referência à agência pelo acronym
        if settings.extraction_agency:
            data['extraction_agency_acronym'] = settings.extraction_agency.acronym
        else:
            data['extraction_agency_acronym'] = None

        return data

