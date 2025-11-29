"""
Formulários para o app cases
"""
from django import forms
from django.utils import timezone
from apps.cases.models import Case
from apps.base_tables.models import AgencyUnit, EmployeePosition, CrimeCategory
from apps.core.models import ExtractionUnit
from apps.requisitions.models import ExtractionRequest
from django.contrib.auth.models import User


class CaseForm(forms.ModelForm):
    """
    Formulário para criar e editar processos de extração
    """
    
    class Meta:
        model = Case
        fields = [
            'extraction_request',
            'requester_agency_unit',
            'request_procedures',
            'crime_category',
            'requested_device_amount',
            'requester_reply_email',
            'requester_authority_name',
            'requester_authority_position',
            'extraction_unit',
            'priority',
            'assigned_to',
            'additional_info',
        ]
        widgets = {
            'extraction_request': forms.Select(attrs={
                'class': 'form-select',
            }),
            'requester_agency_unit': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'request_procedures': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: IP 123/2024, PJ 456/2024',
                'required': True
            }),
            'crime_category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'requested_device_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
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
            'extraction_unit': forms.Select(attrs={
                'class': 'form-select',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select',
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Informações adicionais sobre o processo'
            }),
        }
        labels = {
            'extraction_request': 'Solicitação de Extração',
            'requester_agency_unit': 'Unidade Solicitante',
            'request_procedures': 'Procedimentos',
            'crime_category': 'Categoria de Crime',
            'requested_device_amount': 'Quantidade de Dispositivos',
            'requester_reply_email': 'E-mail para Resposta',
            'requester_authority_name': 'Nome da Autoridade',
            'requester_authority_position': 'Cargo da Autoridade',
            'extraction_unit': 'Unidade de Extração',
            'priority': 'Prioridade',
            'assigned_to': 'Atribuído a',
            'additional_info': 'Informações Adicionais',
        }
        help_texts = {
            'extraction_request': 'Solicitação de extração vinculada (opcional)',
            'requester_agency_unit': 'Unidade que está fazendo a solicitação',
            'request_procedures': 'Número dos procedimentos relacionados (IP, PJ, etc)',
            'crime_category': 'Tipo de crime relacionado à investigação',
            'requested_device_amount': 'Número de dispositivos a serem extraídos',
            'requester_reply_email': 'E-mail para envio de respostas',
            'requester_authority_name': 'Nome completo da autoridade responsável',
            'requester_authority_position': 'Cargo da autoridade',
            'extraction_unit': 'Unidade responsável pela extração',
            'priority': 'Nível de prioridade do processo',
            'assigned_to': 'Usuário responsável pelo processo',
            'additional_info': 'Qualquer informação adicional relevante',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Ordena os querysets
        self.fields['extraction_request'].queryset = ExtractionRequest.objects.filter(
            deleted_at__isnull=True,
            case__isnull=True  # Apenas solicitações sem processo vinculado
        ).order_by('-requested_at')
        self.fields['requester_agency_unit'].queryset = AgencyUnit.objects.all().order_by('acronym')
        self.fields['extraction_unit'].queryset = ExtractionUnit.objects.all().order_by('acronym')
        self.fields['requester_authority_position'].queryset = EmployeePosition.objects.all().order_by('-default_selection', 'name')
        self.fields['crime_category'].queryset = CrimeCategory.objects.all().order_by('-default_selection', 'name')
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        
        # Torna campos opcionais
        self.fields['extraction_request'].required = False
        self.fields['extraction_unit'].required = False
        self.fields['assigned_to'].required = False

    def clean_requested_device_amount(self):
        amount = self.cleaned_data.get('requested_device_amount')
        if amount and amount < 1:
            raise forms.ValidationError('A quantidade deve ser no mínimo 1.')
        return amount


class CaseSearchForm(forms.Form):
    """
    Formulário para busca/filtro de processos
    """
    search = forms.CharField(
        required=False,
        label='Pesquisar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pesquisar por número, procedimentos, autoridade...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        label='Status',
        choices=[('', 'Todos')] + Case.CASE_STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    priority = forms.ChoiceField(
        required=False,
        label='Prioridade',
        choices=[('', 'Todas')] + Case.PRIORITY_CHOICES,
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
    
    assigned_to = forms.ModelChoiceField(
        required=False,
        label='Atribuído a',
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'username'),
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
