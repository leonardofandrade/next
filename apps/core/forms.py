"""
Forms para o app core
"""
from django import forms
from .models import (
    ExtractionAgency, ExtractionUnit, DispatchTemplate,
    ExtractorUser, ExtractionUnitExtractor,
    ExtractionUnitStorageMedia, ExtractionUnitEvidenceLocation,
    GeneralSettings, EmailSettings, ReportsSettings
)


class ExtractionAgencyForm(forms.ModelForm):
    """Form para Agência de Extração"""
    
    # Campo customizado para upload de logo
    main_logo_upload = forms.ImageField(
        required=False,
        label='Logo Principal',
        help_text='Faça upload de uma imagem (PNG, JPG, GIF, WebP)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
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
    
    def save(self, commit=True):
        """Salva a agência convertendo o logo para binário"""
        instance = super().save(commit=False)
        
        # Se há um logo novo, converte para binário
        uploaded_file = self.cleaned_data.get('main_logo_upload')
        if uploaded_file:
            instance.main_logo = uploaded_file.read()
        
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
            'reply_email_subject': forms.TextInput(attrs={'class': 'form-control'})
        }


class DispatchTemplateForm(forms.ModelForm):
    """Form para Template de Ofício"""
    
    # Campo customizado para upload de arquivo (não é um campo do modelo)
    template_file_upload = forms.FileField(
        required=False,
        label='Arquivo Template',
        help_text='Faça upload de um arquivo ODT',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.odt'})
    )
    
    class Meta:
        model = DispatchTemplate
        fields = [
            'extraction_unit', 'name', 'description',
            'template_filename',
            'is_active', 'is_default'
        ]
        widgets = {
            'extraction_unit': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template_filename': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extraction_unit'].queryset = ExtractionUnit.objects.filter(deleted_at__isnull=True)
        
        # Se estiver editando, mostra o nome do arquivo atual
        if self.instance and self.instance.pk and self.instance.template_filename:
            self.fields['template_filename'].initial = self.instance.template_filename
            self.fields['template_filename'].widget.attrs['readonly'] = True
            self.fields['template_file_upload'].help_text = f'Arquivo atual: {self.instance.template_filename}. Faça upload de um novo arquivo para substituir.'
    
    def clean_template_file_upload(self):
        """Valida o arquivo template"""
        file = self.cleaned_data.get('template_file_upload')
        
        if file:
            # Verifica se é um arquivo ODT pela extensão
            if hasattr(file, 'name'):
                if not file.name.lower().endswith('.odt'):
                    raise forms.ValidationError('Apenas arquivos ODT são permitidos.')
        
        return file
    
    def save(self, commit=True):
        """Salva o template convertendo o arquivo para binário"""
        instance = super().save(commit=False)
        
        # Se há um arquivo novo, converte para binário
        uploaded_file = self.cleaned_data.get('template_file_upload')
        if uploaded_file:
            instance.template_file = uploaded_file.read()
            instance.template_filename = uploaded_file.name
        
        if commit:
            instance.save()
        
        return instance


class ExtractorUserForm(forms.ModelForm):
    """Form para Usuário Extrator"""
    
    class Meta:
        model = ExtractorUser
        fields = ['user', 'extraction_agency']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'extraction_agency': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        self.fields['extraction_agency'].queryset = ExtractionAgency.objects.filter(deleted_at__isnull=True)


class ExtractionUnitExtractorForm(forms.ModelForm):
    """Form para Extrator de Unidade de Extração"""
    
    class Meta:
        model = ExtractionUnitExtractor
        fields = ['extraction_unit', 'extractor']
        widgets = {
            'extraction_unit': forms.Select(attrs={'class': 'form-select'}),
            'extractor': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extraction_unit'].queryset = ExtractionUnit.objects.filter(deleted_at__isnull=True)
        self.fields['extractor'].queryset = ExtractorUser.objects.filter(deleted_at__isnull=True)


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extraction_unit'].queryset = ExtractionUnit.objects.filter(deleted_at__isnull=True)


class ExtractionUnitEvidenceLocationForm(forms.ModelForm):
    """Form para Localização de Evidências"""
    
    class Meta:
        model = ExtractionUnitEvidenceLocation
        fields = ['extraction_unit', 'type', 'name', 'description']
        widgets = {
            'extraction_unit': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extraction_unit'].queryset = ExtractionUnit.objects.filter(deleted_at__isnull=True)


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extraction_agency'].queryset = ExtractionAgency.objects.filter(deleted_at__isnull=True)


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
            'email_host_password': forms.PasswordInput(attrs={'class': 'form-control', 'render_value': True}),
            'email_from_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extraction_agency'].queryset = ExtractionAgency.objects.filter(deleted_at__isnull=True)


class ReportsSettingsForm(forms.ModelForm):
    """Form para Configurações de Relatórios"""
    
    # Campos customizados para upload de logos
    default_report_header_logo_upload = forms.ImageField(
        required=False,
        label='Logo do Relatório',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    secondary_report_header_logo_upload = forms.ImageField(
        required=False,
        label='Logo Secundária do Relatório',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
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
        self.fields['extraction_agency'].queryset = ExtractionAgency.objects.filter(deleted_at__isnull=True)
    
    def save(self, commit=True):
        """Salva as configurações convertendo os logos para binário"""
        instance = super().save(commit=False)
        
        # Se há logos novos, converte para binário
        default_logo = self.cleaned_data.get('default_report_header_logo_upload')
        if default_logo:
            instance.default_report_header_logo = default_logo.read()
        
        secondary_logo = self.cleaned_data.get('secondary_report_header_logo_upload')
        if secondary_logo:
            instance.secondary_report_header_logo = secondary_logo.read()
        
        if commit:
            instance.save()
        
        return instance
