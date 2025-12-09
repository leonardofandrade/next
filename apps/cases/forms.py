"""
Formulários para o app cases
"""
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.cases.models import Case, CaseDevice, CaseProcedure
from apps.base_tables.models import AgencyUnit, EmployeePosition, CrimeCategory, DeviceCategory, DeviceModel, ProcedureCategory
from apps.core.models import ExtractionUnit
from apps.requisitions.models import ExtractionRequest
from django.contrib.auth.models import User


class CaseCreateForm(forms.ModelForm):
    """
    Formulário para criar processos de extração
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
                'class': 'form-select select2',
                'data-placeholder': 'Digite para pesquisar...',
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
        # Na criação, apenas solicitações sem processo vinculado
        self.fields['extraction_request'].queryset = ExtractionRequest.objects.filter(
            deleted_at__isnull=True,
            case__isnull=True
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


class CaseUpdateForm(forms.ModelForm):
    """
    Formulário para atualizar processos de extração
    """
    
    class Meta:
        model = Case
        fields = [
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
            'requester_agency_unit': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Digite para pesquisar...',
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
                'rows': 1,
                'placeholder': 'Informações adicionais sobre o processo'
            }),
        }
        labels = {
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
        self.fields['requester_agency_unit'].queryset = AgencyUnit.objects.all().order_by('acronym')
        self.fields['extraction_unit'].queryset = ExtractionUnit.objects.all().order_by('acronym')
        self.fields['requester_authority_position'].queryset = EmployeePosition.objects.all().order_by('-default_selection', 'name')
        self.fields['crime_category'].queryset = CrimeCategory.objects.all().order_by('-default_selection', 'name')
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        
        self.fields['extraction_unit'].required = True
        self.fields['requester_agency_unit'].required = True
        self.fields['request_procedures'].required = True
        self.fields['requested_device_amount'].required = True
        
        # Torna campos opcionais
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


class CaseDeviceForm(forms.ModelForm):
    """
    Formulário para criar e editar dispositivos de um processo
    """
    
    class Meta:
        model = CaseDevice
        fields = [
            'device_category',
            'device_model',
            'color',
            'is_imei_unknown',
            'imei_01',
            'imei_02',
            'imei_03',
            'imei_04',
            'imei_05',
            'owner_name',
            'internal_storage',
            'is_turned_on',
            'is_locked',
            'is_password_known',
            'password_type',
            'password',
            'is_damaged',
            'damage_description',
            'has_fluids',
            'fluids_description',
            'has_sim_card',
            'sim_card_info',
            'has_memory_card',
            'memory_card_info',
            'has_other_accessories',
            'other_accessories_info',
            'is_sealed',
            'security_seal',
            'additional_info',
        ]
        widgets = {
            'device_category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'device_model': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Digite para pesquisar...',
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Preto, Branco, Azul...'
            }),
            'is_imei_unknown': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'imei_01': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IMEI 01',
                'maxlength': '50'
            }),
            'imei_02': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IMEI 02',
                'maxlength': '50'
            }),
            'imei_03': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IMEI 03',
                'maxlength': '50'
            }),
            'imei_04': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IMEI 04',
                'maxlength': '50'
            }),
            'imei_05': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IMEI 05',
                'maxlength': '50'
            }),
            'owner_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do proprietário',
                'maxlength': '200'
            }),
            'internal_storage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 128, 256, 512',
                'min': '1'
            }),
            'is_turned_on': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_locked': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_password_known': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'password_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'password': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '100',
                'placeholder': 'Digite a senha'
            }),
            'is_damaged': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'damage_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descreva os danos',
                'maxlength': '200'
            }),
            'has_fluids': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'fluids_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: sangue, água, óleo...',
                'maxlength': '200'
            }),
            'has_sim_card': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'sim_card_info': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Informações do chip',
                'maxlength': '200'
            }),
            'has_memory_card': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'memory_card_info': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Informações do cartão de memória',
                'maxlength': '200'
            }),
            'has_other_accessories': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'other_accessories_info': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Capa, Carregador...',
                'maxlength': '200'
            }),
            'is_sealed': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'security_seal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número do lacre',
                'maxlength': '100'
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Informações adicionais sobre o dispositivo'
            }),
        }
        labels = {
            'device_category': 'Categoria',
            'device_model': 'Modelo',
            'color': 'Cor',
            'is_imei_unknown': 'IMEI Desconhecido',
            'imei_01': 'IMEI 01',
            'imei_02': 'IMEI 02',
            'imei_03': 'IMEI 03',
            'imei_04': 'IMEI 04',
            'imei_05': 'IMEI 05',
            'owner_name': 'Nome do Proprietário',
            'internal_storage': 'Armazenamento Interno (GB)',
            'is_turned_on': 'Ligado',
            'is_locked': 'Bloqueado',
            'is_password_known': 'Senha Conhecida',
            'password_type': 'Tipo de Senha',
            'password': 'Senha',
            'is_damaged': 'Danificado',
            'damage_description': 'Descrição dos Danos',
            'has_fluids': 'Presença de Fluidos',
            'fluids_description': 'Descrição dos Fluidos',
            'has_sim_card': 'Chip SIM',
            'sim_card_info': 'Informações do Chip',
            'has_memory_card': 'Cartão de Memória',
            'memory_card_info': 'Informações do Cartão de Memória',
            'has_other_accessories': 'Outros Acessórios',
            'other_accessories_info': 'Informações dos Outros Acessórios',
            'is_sealed': 'Lacrado',
            'security_seal': 'Número do Lacre',
            'additional_info': 'Informações Adicionais',
        }

    def __init__(self, *args, **kwargs):
        self.case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        
        # Ordena os querysets
        self.fields['device_category'].queryset = DeviceCategory.objects.filter(
            deleted_at__isnull=True
        ).order_by('-default_selection', 'name')
        self.fields['device_model'].queryset = DeviceModel.objects.filter(
            deleted_at__isnull=True
        ).select_related('brand').order_by('brand__name', 'name')
        
        # Garante que device_category é obrigatório (já é no modelo, mas reforça)
        self.fields['device_category'].required = True
        
        # Torna campos opcionais
        self.fields['owner_name'].required = False
        self.fields['password_type'].required = False
        self.fields['device_model'].required = False
        
        # Configura campos booleanos para não serem obrigatórios
        boolean_fields = [
            'is_turned_on', 'is_locked', 'is_password_known', 'is_damaged',
            'has_fluids', 'has_sim_card', 'has_memory_card', 
            'has_other_accessories', 'is_sealed', 'is_imei_unknown'
        ]
        for field_name in boolean_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        self.fields['device_category'].empty_label = None

    def clean(self):
        cleaned_data = super().clean()
        
        # Normaliza os IMEIs removendo espaços em branco
        for i in range(1, 6):  # imei_01 até imei_05
            imei_field = f'imei_{i:02d}'
            if imei_field in cleaned_data and cleaned_data[imei_field]:
                cleaned_data[imei_field] = cleaned_data[imei_field].strip() or None
        
        return cleaned_data


class CaseProcedureForm(forms.ModelForm):
    """
    Formulário para criar e editar procedimentos de um processo
    """
    
    # Campo customizado para upload de arquivo (não é um campo do modelo)
    document_file = forms.FileField(
        required=False,
        label='Arquivo do Documento',
        help_text='Arquivo do documento relacionado (opcional)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
        })
    )
    
    class Meta:
        model = CaseProcedure
        fields = [
            'procedure_category',
            'number',
        ]
        widgets = {
            'procedure_category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 123/2024',
            }),
        }
        labels = {
            'procedure_category': 'Categoria',
            'number': 'Número',
        }
        help_texts = {
            'procedure_category': 'Categoria do procedimento (IP, PJ, etc)',
            'number': 'Número do procedimento',
        }

    def __init__(self, *args, **kwargs):
        self.case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        
        # Ordena os querysets
        self.fields['procedure_category'].queryset = ProcedureCategory.objects.filter(
            deleted_at__isnull=True
        ).order_by('-default_selection', 'name')
        
        # Torna campos opcionais
        self.fields['procedure_category'].required = False
        self.fields['number'].required = False
        
        # Se não estiver editando (criando novo), pré-seleciona a categoria padrão
        if not self.instance or not self.instance.pk:
            default_category = ProcedureCategory.objects.filter(
                deleted_at__isnull=True,
                default_selection=True
            ).first()
            if default_category:
                self.fields['procedure_category'].initial = default_category.pk

    def clean(self):
        cleaned_data = super().clean()
        procedure_category = cleaned_data.get('procedure_category')
        number = cleaned_data.get('number')
        
        # Validação: se tem categoria, deve ter número
        if procedure_category and not number:
            raise forms.ValidationError({
                'number': 'É necessário informar o número quando uma categoria é selecionada.'
            })
        
        # Validação de unicidade
        if self.case and procedure_category and number:
            queryset = CaseProcedure.objects.filter(
                case=self.case,
                procedure_category=procedure_category,
                number=number,
                deleted_at__isnull=True
            )
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError({
                    'number': f'Já existe um procedimento com categoria {procedure_category.acronym} e número {number} para este processo.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        procedure = super().save(commit=False)
        if self.case:
            procedure.case = self.case
        
        # Processar arquivo se fornecido
        if 'document_file' in self.cleaned_data and self.cleaned_data['document_file']:
            file = self.cleaned_data['document_file']
            procedure.original_filename = file.name
            procedure.content_type = file.content_type
            procedure.document_file = file.read()
        # Se não foi fornecido um novo arquivo, mantém o existente (não altera)
        
        if commit:
            procedure.save()
        return procedure


class CaseCompleteRegistrationForm(forms.Form):
    """
    Formulário para finalizar o cadastro de um processo
    """
    create_extractions = forms.BooleanField(
        required=False,
        initial=True,
        label='Criar extrações automaticamente',
        help_text='Marca esta opção para criar automaticamente as extrações para todos os dispositivos cadastrados.',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    notes = forms.CharField(
        required=False,
        label='Observações',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações sobre a finalização do cadastro (opcional)...'
        })
    )
