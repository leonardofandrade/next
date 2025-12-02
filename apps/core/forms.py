from django import forms
from django.utils.translation import gettext_lazy as _
from apps.core.models import (
    ExtractionAgency, 
    ExtractionUnit,
    ExtractorUser,
    ExtractionUnitExtractor,
    ExtractionUnitStorageMedia,
    ExtractionUnitEvidenceLocation,
    GeneralSettings,
    EmailSettings,
    ReportsSettings,
    ExtractionUnitSettings
)


class ExtractionAgencyForm(forms.ModelForm):
    """Form para Agência de Extração"""
    
    main_logo_file = forms.ImageField(
        required=False,
        label=_('Logo Principal'),
        help_text=_('Formatos aceitos: PNG, JPEG, GIF, WebP')
    )
    
    class Meta:
        model = ExtractionAgency
        fields = ['acronym', 'name', 'incharge_name', 'incharge_position']
        widgets = {
            'acronym': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'incharge_name': forms.TextInput(attrs={'class': 'form-control'}),
            'incharge_position': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['main_logo_file'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Processar upload do logo
        if 'main_logo_file' in self.files:
            logo_file = self.files['main_logo_file']
            instance.main_logo = logo_file.read()
        
        if commit:
            instance.save()
        return instance


class ExtractionUnitForm(forms.ModelForm):
    """Form para Unidade de Extração"""
    
    class Meta:
        model = ExtractionUnit
        fields = [
            'agency', 'acronym', 'name',
            'primary_phone', 'secondary_phone',
            'primary_email', 'secondary_email',
            'address_line1', 'address_number', 'address_line2',
            'neighborhood', 'city_name', 'postal_code', 'state_name', 'country_name',
            'incharge_name', 'incharge_position',
            'reply_email_template', 'reply_email_subject'
        ]
        widgets = {
            'agency': forms.Select(attrs={'class': 'form-select'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'secondary_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'secondary_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control'}),
            'city_name': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'state_name': forms.TextInput(attrs={'class': 'form-control'}),
            'country_name': forms.TextInput(attrs={'class': 'form-control'}),
            'incharge_name': forms.TextInput(attrs={'class': 'form-control'}),
            'incharge_position': forms.TextInput(attrs={'class': 'form-control'}),
            'reply_email_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'reply_email_subject': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ExtractorUserForm(forms.ModelForm):
    """Form para Usuário Extrator"""
    
    class Meta:
        model = ExtractorUser
        fields = ['user', 'extraction_agency']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'extraction_agency': forms.Select(attrs={'class': 'form-select'}),
        }


class ExtractionUnitExtractorForm(forms.ModelForm):
    """Form para Extrator de Unidade"""
    
    class Meta:
        model = ExtractionUnitExtractor
        fields = ['extraction_unit', 'extractor']
        widgets = {
            'extraction_unit': forms.Select(attrs={'class': 'form-select'}),
            'extractor': forms.Select(attrs={'class': 'form-select'}),
        }


class ExtractionUnitStorageMediaForm(forms.ModelForm):
    """Form para Meio de Armazenamento"""
    
    class Meta:
        model = ExtractionUnitStorageMedia
        fields = ['extraction_unit', 'acronym', 'name', 'description']
        widgets = {
            'extraction_unit': forms.Select(attrs={'class': 'form-select'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ExtractionUnitEvidenceLocationForm(forms.ModelForm):
    """Form para Local de Armazenamento de Evidências"""
    
    class Meta:
        model = ExtractionUnitEvidenceLocation
        fields = ['extraction_unit', 'type', 'name', 'description', 'shelf_name', 'slot_name']
        widgets = {
            'extraction_unit': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shelf_name': forms.TextInput(attrs={'class': 'form-control'}),
            'slot_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class GeneralSettingsForm(forms.ModelForm):
    """Form para Configurações Gerais"""
    
    class Meta:
        model = GeneralSettings
        fields = [
            'extraction_agency', 'system_name', 'system_version', 'system_description',
            'primary_color', 'secondary_color',
            'maintenance_mode', 'maintenance_message',
            'backup_enabled', 'backup_frequency'
        ]
        widgets = {
            'extraction_agency': forms.Select(attrs={'class': 'form-select'}),
            'system_name': forms.TextInput(attrs={'class': 'form-control'}),
            'system_version': forms.TextInput(attrs={'class': 'form-control'}),
            'system_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'backup_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'backup_frequency': forms.Select(attrs={'class': 'form-select'}),
        }


class EmailSettingsForm(forms.ModelForm):
    """Form para Configurações de E-mail"""
    
    class Meta:
        model = EmailSettings
        fields = [
            'extraction_agency', 'email_host', 'email_port',
            'email_use_tls', 'email_use_ssl',
            'email_host_user', 'email_host_password',
            'email_from_name'
        ]
        widgets = {
            'extraction_agency': forms.Select(attrs={'class': 'form-select'}),
            'email_host': forms.TextInput(attrs={'class': 'form-control'}),
            'email_port': forms.NumberInput(attrs={'class': 'form-control'}),
            'email_use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_use_ssl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_host_user': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_host_password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'email_from_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ReportsSettingsForm(forms.ModelForm):
    """Form para Configurações de Relatórios"""
    
    default_logo_file = forms.ImageField(
        required=False,
        label=_('Logo Principal do Relatório'),
        help_text=_('Formatos aceitos: PNG, JPEG, GIF, WebP')
    )
    
    secondary_logo_file = forms.ImageField(
        required=False,
        label=_('Logo Secundário do Relatório'),
        help_text=_('Formatos aceitos: PNG, JPEG, GIF, WebP')
    )
    
    class Meta:
        model = ReportsSettings
        fields = [
            'extraction_agency', 'reports_enabled',
            'distribution_report_notes',
            'report_cover_header_line_1', 'report_cover_header_line_2', 'report_cover_header_line_3',
            'report_cover_footer_line_1', 'report_cover_footer_line_2'
        ]
        widgets = {
            'extraction_agency': forms.Select(attrs={'class': 'form-select'}),
            'reports_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'distribution_report_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'report_cover_header_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'report_cover_header_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'report_cover_header_line_3': forms.TextInput(attrs={'class': 'form-control'}),
            'report_cover_footer_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'report_cover_footer_line_2': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['default_logo_file'].widget.attrs.update({'class': 'form-control'})
        self.fields['secondary_logo_file'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Processar upload dos logos
        if 'default_logo_file' in self.files:
            logo_file = self.files['default_logo_file']
            instance.default_report_header_logo = logo_file.read()
        
        if 'secondary_logo_file' in self.files:
            logo_file = self.files['secondary_logo_file']
            instance.secondary_report_header_logo = logo_file.read()
        
        if commit:
            instance.save()
        return instance
