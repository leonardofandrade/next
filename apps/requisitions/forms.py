"""
Formulários para o app requisitions
"""
from django import forms
from django.utils import timezone
from apps.requisitions.models import ExtractionRequest
from apps.base_tables.models import AgencyUnit, EmployeePosition, CrimeCategory
from apps.core.models import ExtractionUnit


class ExtractionRequestForm(forms.ModelForm):
    """
    Formulário para criar e editar solicitações de extração
    """
    
    class Meta:
        model = ExtractionRequest
        fields = [
            'requester_agency_unit',
            'requested_device_amount',
            'extraction_unit',
            'requester_reply_email',
            'requester_authority_name',
            'requester_authority_position',
            'request_procedures',
            'crime_category',
            'additional_info',
        ]
        widgets = {
            'requester_agency_unit': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'requested_device_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'extraction_unit': forms.Select(attrs={
                'class': 'form-select',
            }),
            'requester_reply_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'requester_authority_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo da autoridade'
            }),
            'requester_authority_position': forms.Select(attrs={
                'class': 'form-select',
            }),
            'request_procedures': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: IP 123/2024, PJ 456/2024',
                'required': True
            }),
            'crime_category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Informações adicionais sobre a solicitação'
            }),
        }
        labels = {
            'requester_agency_unit': 'Unidade Solicitante',
            'requested_device_amount': 'Quantidade de Dispositivos',
            'extraction_unit': 'Unidade de Extração',
            'requester_reply_email': 'E-mail para Resposta',
            'requester_authority_name': 'Nome da Autoridade',
            'requester_authority_position': 'Cargo da Autoridade',
            'request_procedures': 'Procedimentos',
            'crime_category': 'Categoria de Crime',
            'additional_info': 'Informações Adicionais',
        }
        help_texts = {
            'requester_agency_unit': 'Unidade que está fazendo a solicitação',
            'requested_device_amount': 'Número de dispositivos a serem extraídos',
            'extraction_unit': 'Unidade responsável pela extração (opcional)',
            'requester_reply_email': 'E-mail para envio de respostas',
            'requester_authority_name': 'Nome completo da autoridade responsável',
            'requester_authority_position': 'Cargo da autoridade (ex: Delegado, Promotor)',
            'request_procedures': 'Número dos procedimentos relacionados (IP, PJ, etc)',
            'crime_category': 'Tipo de crime relacionado à investigação',
            'additional_info': 'Qualquer informação adicional relevante',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Ordena os querysets
        self.fields['requester_agency_unit'].queryset = AgencyUnit.objects.all().order_by('acronym')
        self.fields['extraction_unit'].queryset = ExtractionUnit.objects.all().order_by('acronym')
        self.fields['requester_authority_position'].queryset = EmployeePosition.objects.all().order_by('-default_selection', 'name')
        self.fields['crime_category'].queryset = CrimeCategory.objects.all().order_by('-default_selection', 'name')
        
        # Torna extraction_unit opcional
        self.fields['extraction_unit'].required = False

    def clean_requested_device_amount(self):
        amount = self.cleaned_data.get('requested_device_amount')
        if amount and amount < 1:
            raise forms.ValidationError('A quantidade deve ser no mínimo 1.')
        return amount


class ExtractionRequestSearchForm(forms.Form):
    """
    Formulário para busca/filtro de solicitações
    """
    search = forms.CharField(
        required=False,
        label='Pesquisar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pesquisar por procedimentos, autoridade, etc...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        label='Status',
        choices=[('', 'Todos')] + ExtractionRequest.REQUEST_STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    requester_agency_unit = forms.ModelChoiceField(
        required=False,
        label='Unidade Solicitante',
        queryset=AgencyUnit.objects.all().order_by('acronym'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    extraction_unit = forms.ModelChoiceField(
        required=False,
        label='Unidade de Extração',
        queryset=ExtractionUnit.objects.all().order_by('acronym'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    crime_category = forms.ModelChoiceField(
        required=False,
        label='Categoria de Crime',
        queryset=CrimeCategory.objects.all().order_by('-default_selection', 'name'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        label='Data Inicial',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='Data Final',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
