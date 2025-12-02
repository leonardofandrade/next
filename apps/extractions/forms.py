"""
Formulários para o app extractions
"""
from django import forms
from apps.cases.models import Extraction
from apps.core.models import ExtractionUnit, ExtractionUnitStorageMedia
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


class ExtractionFinishForm(forms.Form):
    """
    Formulário para finalização de extração
    """
    extraction_result = forms.ChoiceField(
        required=True,
        label='Resultado da Extração',
        choices=Extraction.extraction_result_choices,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    finished_notes = forms.CharField(
        required=False,
        label='Observações de Finalização',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações gerais sobre a finalização...'
        })
    )
    
    extraction_results_notes = forms.CharField(
        required=False,
        label='Observações do Resultado',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Detalhes sobre o resultado da extração...'
        })
    )
    
    # Tipos de extração
    logical_extraction = forms.BooleanField(
        required=False,
        label='Extração Lógica',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    logical_extraction_notes = forms.CharField(
        required=False,
        label='Observações da Extração Lógica',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    physical_extraction = forms.BooleanField(
        required=False,
        label='Extração Física',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    physical_extraction_notes = forms.CharField(
        required=False,
        label='Observações da Extração Física',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    full_file_system_extraction = forms.BooleanField(
        required=False,
        label='Extração Completa do Sistema de Arquivos',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    full_file_system_extraction_notes = forms.CharField(
        required=False,
        label='Observações da Extração Completa',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    cloud_extraction = forms.BooleanField(
        required=False,
        label='Extração em Nuvem',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    cloud_extraction_notes = forms.CharField(
        required=False,
        label='Observações da Extração em Nuvem',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    # Cellebrite Premium
    cellebrite_premium = forms.BooleanField(
        required=False,
        label='Cellebrite Premium',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    cellebrite_premium_notes = forms.CharField(
        required=False,
        label='Observações do Cellebrite Premium',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    cellebrite_premium_support = forms.BooleanField(
        required=False,
        label='Suporte Cellebrite Premium',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    cellebrite_premium_support_notes = forms.CharField(
        required=False,
        label='Observações do Suporte Cellebrite Premium',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    # Armazenamento
    extraction_size = forms.IntegerField(
        required=False,
        label='Tamanho da Extração (GB)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'placeholder': '0'
        })
    )
    
    storage_media = forms.ModelChoiceField(
        required=False,
        label='Mídia de Armazenamento',
        queryset=ExtractionUnitStorageMedia.objects.filter(deleted_at__isnull=True),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        extraction_unit = kwargs.pop('extraction_unit', None)
        super().__init__(*args, **kwargs)
        
        # Filtra mídias de armazenamento pela unidade de extração
        if extraction_unit:
            self.fields['storage_media'].queryset = ExtractionUnitStorageMedia.objects.filter(
                extraction_unit=extraction_unit,
                deleted_at__isnull=True
            ).order_by('name')

