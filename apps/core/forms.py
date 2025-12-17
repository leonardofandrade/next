"""
Forms para o app core
"""
from django import forms
from .models import (
    ExtractionAgency, ExtractionUnit, DocumentTemplate,
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


class ExtractionUnitReplyEmailForm(forms.ModelForm):
    """Form (parcial) para editar template de email de resposta da unidade"""

    class Meta:
        model = ExtractionUnit
        fields = ['reply_email_subject', 'reply_email_template']
        widgets = {
            'reply_email_subject': forms.TextInput(attrs={'class': 'form-control'}),
            'reply_email_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 12}),
        }


class DocumentTemplateForm(forms.ModelForm):
    """Form para Template de Documento (ofício)"""

    header_left_logo_upload = forms.ImageField(
        required=False,
        label='Logo do Cabeçalho Esquerdo',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    header_right_logo_upload = forms.ImageField(
        required=False,
        label='Logo do Cabeçalho Direito',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    footer_left_logo_upload = forms.ImageField(
        required=False,
        label='Logo do Rodapé Esquerdo',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    footer_right_logo_upload = forms.ImageField(
        required=False,
        label='Logo do Rodapé Direito',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    watermark_logo_upload = forms.ImageField(
        required=False,
        label='Logo da Água-Marinha',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = DocumentTemplate
        fields = [
            'name', 'description', 'is_default',
            'header_text', 'subject_text', 'body_text', 'signature_text',
            'footer_text', 'watermark_text',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'header_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'subject_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'body_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 12}),
            'signature_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'footer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'watermark_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        mapping = {
            'header_left_logo_upload': 'header_left_logo',
            'header_right_logo_upload': 'header_right_logo',
            'footer_left_logo_upload': 'footer_left_logo',
            'footer_right_logo_upload': 'footer_right_logo',
            'watermark_logo_upload': 'watermark_logo',
        }
        for upload_field, model_field in mapping.items():
            uploaded = self.cleaned_data.get(upload_field)
            if uploaded:
                setattr(instance, model_field, uploaded.read())

        if commit:
            instance.save()
        return instance

