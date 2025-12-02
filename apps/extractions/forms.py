"""
Formulários para o app extractions
"""
from django import forms
from apps.cases.models import Extraction
from apps.core.models import ExtractionUnit
from django.contrib.auth.models import User


class ExtractionSearchForm(forms.Form):
    """
    Formulário para busca/filtro de extrações
    """
    search = forms.CharField(
        required=False,
        label='Pesquisar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pesquisar por modelo, IMEI, proprietário ou número do processo...'
        })
    )
    
    case_number = forms.CharField(
        required=False,
        label='Número do Processo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 123/2024'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        label='Status',
        choices=[('', 'Todos')] + Extraction.EXTRACTION_STATUS_CODES,
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
        queryset=User.objects.filter(
            is_active=True,
            extractor_users__isnull=False
        ).distinct().order_by('first_name', 'username'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    extraction_result = forms.ChoiceField(
        required=False,
        label='Resultado',
        choices=[('', 'Todos')] + Extraction.extraction_result_choices,
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

