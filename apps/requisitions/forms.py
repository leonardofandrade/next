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
                'class': 'form-select select2',
                'data-placeholder': 'Digite para pesquisar...',
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
                'empty_label': None,
            }),
            'request_procedures': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: IP 123/2024, PJ 456/2024',
            }),
            'crime_category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Informações adicionais sobre a solicitação'
            }),
        }
        labels = {
            'requester_agency_unit': 'Unidade Solicitante',
            'requested_device_amount': 'Dispositivos',
            'extraction_unit': 'Distribuir para',
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
            'extraction_unit': 'Unidade responsável pela extração',
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
        
        # Define campos obrigatórios
        self.fields['requester_agency_unit'].required = True
        self.fields['requested_device_amount'].required = True
        self.fields['request_procedures'].required = True
        self.fields['extraction_unit'].required = True

        self.fields['requester_authority_position'].empty_label = None

    def clean(self):
        cleaned_data = super().clean()
        
        # Valida campos obrigatórios
        requester_agency_unit = cleaned_data.get('requester_agency_unit')
        requested_device_amount = cleaned_data.get('requested_device_amount')
        request_procedures = cleaned_data.get('request_procedures')
        extraction_unit = cleaned_data.get('extraction_unit')
        
        if not requester_agency_unit:
            self.add_error('requester_agency_unit', 'Este campo é obrigatório.')
        
        if not requested_device_amount:
            self.add_error('requested_device_amount', 'Este campo é obrigatório.')
        
        if not request_procedures:
            self.add_error('request_procedures', 'Este campo é obrigatório.')
        
        if not extraction_unit:
            self.add_error('extraction_unit', 'Este campo é obrigatório.')
        
        return cleaned_data

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
