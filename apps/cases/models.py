from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.core.models import (
    AuditedModel, AbstractCaseModel, ExtractionUnit, 
    ExtractionUnitStorageMedia, ExtractorUser
    )
from apps.base_tables.models import ProcedureCategory
from apps.requisitions.models import ExtractionRequest
from apps.core.models import AbstractDeviceModel


class Case(AbstractCaseModel):
    """ Model for Cases """

    CASE_STATUS_DRAFT = 'draft'
    CASE_STATUS_WAITING_EXTRACTOR = 'waiting_extractor'
    CASE_STATUS_WAITING_START = 'waiting_start'
    CASE_STATUS_IN_PROGRESS = 'in_progress'
    CASE_STATUS_PAUSED = 'paused'
    CASE_STATUS_COMPLETED = 'completed'
    CASE_STATUS_WAITING_COLLECT = "waiting_collect"

    CASE_STATUS_CHOICES = [
        (CASE_STATUS_DRAFT, _('Cadastrto Incompleto')),
        (CASE_STATUS_WAITING_EXTRACTOR, _('Aguardando Extrator')),
        (CASE_STATUS_WAITING_START, _('Aguardando início')),
        (CASE_STATUS_IN_PROGRESS, _('Em progresso')),
        (CASE_STATUS_PAUSED, _('Pausado')),
        (CASE_STATUS_COMPLETED, _('Concluído')),
        (CASE_STATUS_WAITING_COLLECT, _('Aguardando coleta')),
    ]

    
    number = models.CharField(
        null=True,
        blank=True,
        max_length=50,
        help_text=_("Número do processo.")
    )
    year = models.IntegerField(
        null=True,
        blank=True,
        editable=False,
        help_text=_("Ano do processo para controle de numeração sequencial (controlado pelo sistema).")
    )
    status = models.CharField(
        max_length=50,
        choices=CASE_STATUS_CHOICES,
        default=CASE_STATUS_DRAFT,
        blank=False,
        null=False,
        help_text=_("Status do processo.")
    )
    PRIORITY_CHOICES = [
        (0, 'Baixa'),
        (1, 'Média'),
        (2, 'Alta'),
        (3, 'Urgente'),
    ]

    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=0,
        blank=False,
        null=False,
        help_text=_("Prioridade do processo.")
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_extraction_cases',
        null=True,
        blank=True,
        help_text=_("Usuário responsável pelo processo.")
    )
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Data em que o processo foi atribuída.")
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_by_extraction_cases',
        null=True,
        blank=True,
        help_text=_("atribuído por")
    )
    extraction_request = models.OneToOneField(
        ExtractionRequest,
        on_delete=models.SET_NULL,
        related_name='case',
        null=True,
        blank=True,
        help_text=_("Solicitação de extração.")
    )

    registration_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Data em que o cadastro do processo foi completado.")
    )
    
    # Case completation fields
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Data em que o processo foi finalizado.")
    )
    finished_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='finished_by_extraction_cases',
        null=True,
        blank=True,
        help_text=_("finalizado por")
    )
    finalization_notes = models.TextField(
        blank=True,
        null=True,
        help_text=_("Observações sobre a finalização do processo.")
    )
    dispatch_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Número do ofício de resposta do processo.")
    )
    dispatch_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Data do ofício de resposta do processo.")
    )
    dispatch_file = models.BinaryField(
        blank=True,
        null=True,
        help_text=_("Arquivo do ofício de resposta do processo.")
    )
    dispatch_filename = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Nome original do arquivo do ofício de resposta do processo.")
    )
    dispatch_content_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Tipo de conteúdo do arquivo do ofício de resposta do processo (MIME type).")
    )
    # end of case finalization fields
    
    # Legacy fields
    is_legacy = models.BooleanField(
        default=False,
        help_text=_("Campo para identificar extrações legadas.")
    )
    legacy_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Número legado do processo.")
    )
    legacy_notes = models.TextField(
        blank=True,
        null=True,
        help_text=_("Observações legadas do processo.")
    )
    
    
    class Meta:
        db_table = 'case'
        verbose_name = "Processo"
        verbose_name_plural = "Processos"
        unique_together = ('extraction_unit', 'year', 'number')
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['extraction_unit']),
            models.Index(fields=['year']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
        ]


    def __str__(self):
        if self.number:
            return f"{self.number}"
        else:
            return "N/A"
    
    
    def get_priority_color(self):
        """Returns Bootstrap color class based on priority"""
        priority_colors = {
            0: 'secondary',
            1: 'primary',
            2: 'warning',
            3: 'danger',
        }
        return priority_colors.get(self.priority, 'secondary')
    
    def get_priority_display(self):
        """Returns the priority display"""
        return self.PRIORITY_CHOICES[self.priority][1]

    def get_status_color(self):
        """Returns Bootstrap color class based on status"""
        status_colors = {
            self.CASE_STATUS_DRAFT: 'secondary',
            self.CASE_STATUS_WAITING_EXTRACTOR: 'warning',
            self.CASE_STATUS_WAITING_START: 'warning',
            self.CASE_STATUS_IN_PROGRESS: 'primary',
            self.CASE_STATUS_PAUSED: 'secondary',
            self.CASE_STATUS_COMPLETED: 'success',
            self.CASE_STATUS_WAITING_COLLECT: 'warning',
        }
        return status_colors.get(self.status, 'secondary')
    
    @property
    def status_badge_class(self):
        """Returns complete Bootstrap badge class for status"""
        return f"bg-{self.get_status_color()}"
    
    def generate_case_number(self):
        """
        Gera o número do processo no formato: AAAA.UUU.NNNN
        Onde:
        - AAAA = Ano corrente (4 dígitos)
        - UUU = ID da extraction_unit (3 dígitos preenchidos com zeros)
        - NNNN = Próximo número sequencial da extraction_unit (reiniciado todo ano)
        
        Retorna o número gerado ou None se não houver extraction_unit
        """
        if not self.extraction_unit:
            return None
        
        current_year = timezone.now().year
        extraction_unit_id = self.extraction_unit.pk
        
        # Busca todos os casos da extraction_unit no ano corrente para encontrar o maior número sequencial
        cases = Case.objects.filter(
            extraction_unit=self.extraction_unit,
            year=current_year,
            number__isnull=False,
            deleted_at__isnull=True
        ).exclude(
            pk=self.pk  # Exclui o próprio caso se estiver sendo atualizado
        ).values_list('number', flat=True)
        
        # Extrai o maior número sequencial dos casos existentes
        max_sequential = 0
        for case_number in cases:
            if case_number:
                # Formato esperado: AAAA.UUU.NNNN
                # Extrai apenas a parte sequencial (NNNN)
                parts = case_number.split('.')
                if len(parts) == 3:
                    try:
                        # Verifica se o ano e extraction_unit correspondem
                        case_year = int(parts[0])
                        case_unit_id = int(parts[1])
                        if case_year == current_year and case_unit_id == extraction_unit_id:
                            sequential = int(parts[2])
                            if sequential > max_sequential:
                                max_sequential = sequential
                    except (ValueError, IndexError):
                        continue
        
        # Próximo número sequencial
        next_sequential = max_sequential + 1
        
        # Formata o número: AAAA.UUU.NNNN
        case_number = f"{current_year}.{extraction_unit_id:03d}.{next_sequential:04d}"
        
        return case_number
    
    def update_status_based_on_extractions(self):
        """
        Atualiza o status do Case baseado no status das extrações
        
        Regras:
        - Se não houver extrações ou todas forem 'pending': WAITING_EXTRACTOR
        - Se pelo menos uma estiver 'assigned': WAITING_START
        - Se pelo menos uma estiver 'in_progress': IN_PROGRESS
        - Se todas estiverem 'paused': PAUSED
        - Se todas estiverem 'completed': COMPLETED
        - Mix de estados: IN_PROGRESS (estado predominante quando há atividade)
        """
        # Busca todas as extrações não deletadas do case
        extractions = self.case_devices.filter(
            deleted_at__isnull=True
        ).exclude(
            device_extraction__isnull=True
        ).values_list(
            'device_extraction__status', 
            flat=True
        )
        
        # Se não houver extrações, mantém o status atual ou volta para draft
        if not extractions:
            if self.status not in [self.CASE_STATUS_DRAFT, self.CASE_STATUS_WAITING_COLLECT]:
                self.status = self.CASE_STATUS_DRAFT
                self.save(update_fields=['status'])
            return
        
        extraction_statuses = list(extractions)
        total = len(extraction_statuses)
        
        # Conta quantas extrações estão em cada status
        pending_count = extraction_statuses.count('pending')
        assigned_count = extraction_statuses.count('assigned')
        in_progress_count = extraction_statuses.count('in_progress')
        paused_count = extraction_statuses.count('paused')
        completed_count = extraction_statuses.count('completed')
        
        # Lógica de decisão do status do Case
        new_status = None
        
        # Se todas estiverem completas
        if completed_count == total:
            new_status = self.CASE_STATUS_COMPLETED
        
        # Se alguma estiver em progresso (prioridade alta)
        elif in_progress_count > 0:
            new_status = self.CASE_STATUS_IN_PROGRESS
        
        # Se todas estiverem pausadas
        elif paused_count == total:
            new_status = self.CASE_STATUS_PAUSED
        
        # Se todas estiverem pausadas e/ou completas, mas pelo menos uma pausada
        elif paused_count > 0 and (paused_count + completed_count) == total:
            new_status = self.CASE_STATUS_PAUSED
        
        # Se alguma estiver atribuída (aguardando início)
        elif assigned_count > 0:
            new_status = self.CASE_STATUS_WAITING_START
        
        # Se todas estiverem pendentes (aguardando extrator)
        elif pending_count == total:
            new_status = self.CASE_STATUS_WAITING_EXTRACTOR
        
        # Caso padrão: mix de estados, considera em progresso
        else:
            new_status = self.CASE_STATUS_IN_PROGRESS
        
        # Atualiza o status se houver mudança
        if new_status and self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])
    

class CaseProcedure(AuditedModel):
    """ Model for Case Procedures """
    case = models.ForeignKey(
        Case,
        on_delete=models.PROTECT,
        related_name='procedures',
        help_text=_("Processo.")
    )
    number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Número do procedimento.")
    )
    procedure_category = models.ForeignKey(
        ProcedureCategory,
        on_delete=models.PROTECT,
        related_name='case_procedures',
        null=True,
        blank=True,
        help_text=_("Categoria do procedimento.")
    )
    document_file = models.BinaryField(
        blank=True,
        null=True,
        help_text=_("Arquivo do documento.")
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Nome original do arquivo.")
    )
    content_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Tipo de conteúdo do arquivo (MIME type).")
    )

    class Meta:
        db_table = 'case_procedure'
        verbose_name = "Procedimento do Processo"
        verbose_name_plural = "Procedimentos do Processo"
        unique_together = ('case', 'number', 'procedure_category')
        indexes = [
            models.Index(fields=['case']),
            models.Index(fields=['created_at']),
        ]
        

class CaseDevice(AbstractDeviceModel):
    
    """Model for Case Devices"""
    case = models.ForeignKey(
        Case,
        on_delete=models.PROTECT,
        related_name='case_devices',
        null=False,
        blank=False,
        help_text=_("Processo relacionado a este dispositivo")
    )

    class Meta:
        db_table = 'case_device'
        verbose_name = _('Dispositivo do Processo')
        verbose_name_plural = _('Dispositivos do Processo')
        indexes = [
            models.Index(fields=['case']),
            models.Index(fields=['device_model']),
            models.Index(fields=['created_at']),
        ]
                
class Extraction(AuditedModel):
    """ Model for Extractions """
    STATUS_PENDING = 'pending'
    STATUS_ASSIGNED = 'assigned'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_PAUSED = 'paused'
    STATUS_COMPLETED = 'completed'

    EXTRACTION_STATUS_CODES = [
        (STATUS_PENDING, 'Aguardando Extrator'),
        (STATUS_ASSIGNED, 'Aguardando Início'),
        (STATUS_IN_PROGRESS, 'Em Andamento'),
        (STATUS_PAUSED, 'Pausado'),
        (STATUS_COMPLETED, 'Finalizada'),
    ]
    
    case_device = models.OneToOneField(
        CaseDevice,
        null=False,
        blank=False,
        default=None,
        on_delete=models.CASCADE,
        related_name='device_extraction',
        verbose_name='Dispositivo'
    )
    status = models.CharField(
        max_length=50,
        choices=EXTRACTION_STATUS_CODES,
        default=STATUS_PENDING,
        blank=False,
        null=False,
        help_text=_("Status da extração.")
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_by_extractions',
        null=True,
        help_text=_("Usuário responsável pela extração.")
    )
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Data de atribuição.")
    )
    assigned_to = models.ForeignKey(
        ExtractorUser,
        on_delete=models.CASCADE,
        related_name='assigned_extractions',
        null=True,
        help_text=_("Usuário responsável pela extração.")
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Data de início da extração.")
    )
    started_by = models.ForeignKey(
        ExtractorUser,
        on_delete=models.CASCADE,
        related_name='started_extractions',
        null=True,
        help_text=_("Usuário que iniciou a extração.")
    )
    started_notes = models.TextField(
        _('Observações do Início da Extração'),
        blank=True,
        null=True,
        help_text=_("Observações sobre o início da extração.")
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Data de término da extração.")
    )
    finished_by = models.ForeignKey(
        ExtractorUser,
        on_delete=models.CASCADE,
        related_name='finished_extractions',
        null=True,
        help_text=_("Usuário que finalizou a extração.")
    )
    finished_notes = models.TextField(
        _('Observações do Término da Extração'),
        blank=True,
        null=True,
        help_text=_("Observações sobre o término da extração.")
    )
    extraction_result_choices = [
        ('success', 'Bem-Sucedida'),
        ('failed', 'Falhou'),
        ('partial', 'Parcial'),
    ]
    extraction_result = models.CharField(
        _('Resultado da Extração'),
        max_length=50,
        choices=extraction_result_choices,
        null=True,
        blank=True,
        help_text=_("Resultado da extração do dispositivo.")
    )
    extraction_results_notes = models.TextField(
        _('Observações do Resultado da Extração'),
        blank=True,
        null=True,
        help_text=_("Observações sobre o resultado da extração.")
    )
    brute_force_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Data de início da força bruta.")
    )
    brute_force_started_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='brute_force_started_extractions',
        null=True,
        help_text=_("Usuário que iniciou a força bruta.")
    )
    brute_force_started_notes = models.TextField(
        _('Observações do Início da Força Bruta'),
        blank=True,
        null=True,
        help_text=_("Observações sobre o início da força bruta.")
    )

    brute_force_finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Data de término da força bruta.")
    )
    brute_force_finished_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='brute_force_finished_extractions',
        null=True,
        help_text=_("Usuário que finalizou a força bruta.")
    )
    brute_force_result  = models.BooleanField(
        _('Força Bruta Bem-Sucedida'),
        default=False,
        help_text=_("Força Bruta bem-sucedida.")
    )
    brute_force_results_notes = models.TextField(
        _('Observações da força bruta'),
        blank=True,
        null=True,
        help_text=_("Observações da força bruta.")
    )
    cellebrite_premium = models.BooleanField(
        _('Cellebrite Premium'),
        default=False,
        help_text=_('Indica se o dispositivo é um Cellebrite Premium')
    )
    cellebrite_premium_notes = models.TextField(
        _('Observações do Cellebrite Premium'),
        blank=True,
        null=True,
        help_text=_("Observações sobre o Cellebrite Premium do dispositivo")
    )
    cellebrite_premium_support = models.BooleanField(
        _('Suporte Cellebrite Premium'),
        default=False,
        help_text=_('Indica se o dispositivo tem suporte a Cellebrite Premium')
    )
    cellebrite_premium_support_notes = models.TextField(
        _('Observações do Suporte Cellebrite Premium'),
        blank=True,
        null=True,
        help_text=_("Observações sobre o suporte a Cellebrite Premium do dispositivo")
    )
    logical_extraction = models.BooleanField(
        _('Extração Lógica'),
        default=False,
        help_text=_('Indica se o dispositivo é uma extração lógica')
    )
    logical_extraction_notes = models.TextField(
        _('Observações da Extração Lógica'),
        blank=True,
        null=True,
        help_text=_("Observações sobre a extração lógica do dispositivo")
    )
    physical_extraction = models.BooleanField(
        _('Extração Física'),
        default=False,
        help_text=_('Indica se o dispositivo é uma extração física')
    )
    physical_extraction_notes = models.TextField(
        _('Observações da Extração Física'),
        blank=True,
        null=True,
        help_text=_("Observações sobre a extração física do dispositivo")
    )
    full_file_system_extraction = models.BooleanField(
        _('Extração Completa do Sistema de Arquivos'),
        default=False,
        help_text=_('Indica se o dispositivo é uma extração completa do sistema de arquivos')
    )
    full_file_system_extraction_notes = models.TextField(
        _('Observações da Extração Completa do Sistema de Arquivos'),
        blank=True,
        null=True,
        help_text=_("Observações sobre a extração completa do sistema de arquivos do dispositivo")
    )
    cloud_extraction = models.BooleanField(
        _('Extração em Nuvem'),
        default=False,
        help_text=_('Indica se o dispositivo é uma extração em nuvem')
    )
    cloud_extraction_notes = models.TextField(
        _('Observações da Extração em Nuvem'),
        blank=True,
        null=True,
        help_text=_("Observações sobre a extração em nuvem do dispositivo")
    )    
    extraction_size = models.PositiveIntegerField(
        _('Tamanho da Extração (GB)'),
        null=True,
        default=0,
        help_text=_('Tamanho da extração em GB')
    )
    storage_media = models.ForeignKey(
        ExtractionUnitStorageMedia,
        on_delete=models.SET_NULL,
        related_name='extractions',
        null=True,
        blank=True,
        help_text=_("Local de armazenamento onde a extração está salva")
    )

    class Meta:
        db_table = 'extraction'
        verbose_name = "Extração"
        verbose_name_plural = "Extrações"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['started_at']),
            models.Index(fields=['finished_at']),
            models.Index(fields=['extraction_result']),
            models.Index(fields=['case_device', 'status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id}"

    def clean(self):
        """Validações de negócio para o modelo Extraction"""
        errors = {}
        
        # Validação: Se status é 'completed', deve ter finished_at
        if self.status == self.STATUS_COMPLETED and not self.finished_at:
            errors['finished_at'] = _('Extração finalizada deve ter data de término.')
        
        # Validação: Se tem brute_force_started_at, deve ter brute_force_finished_at
        if self.brute_force_started_at and not self.brute_force_finished_at:
            errors['brute_force_finished_at'] = _('Força bruta iniciada deve ter data de término.')
        
        # Validação: Tamanho da extração deve ser positivo se informado
        if self.extraction_size and self.extraction_size <= 0:
            errors['extraction_size'] = _('Tamanho da extração deve ser maior que zero.')
        
        # Validação: Se status é 'in_progress', deve ter started_at
        if self.status == self.STATUS_IN_PROGRESS and not self.started_at:
            errors['started_at'] = _('Extração em andamento deve ter data de início.')
        
        # Validação: Se status é 'assigned', deve ter assigned_to
        if self.status == self.STATUS_ASSIGNED and not self.assigned_to:
            errors['assigned_to'] = _('Extração atribuída deve ter um extrator designado.')
        
        if errors:
            raise ValidationError(errors)

    def get_device_imei_list(self):
        """
        Retorna os IMEIs do dispositivo associado.
        """
        if self.case_device:
            return self.case_device.get_device_imei_as_list()
        return "IMEI Não Informado"

    # Métodos de verificação de status
    def can_start_extraction(self):
        """Verifica se a extração pode ser iniciada"""
        return self.status == self.STATUS_ASSIGNED

    def can_pause_extraction(self):
        """Verifica se a extração pode ser pausada"""
        return self.status == self.STATUS_IN_PROGRESS

    def can_complete_extraction(self):
        """Verifica se a extração pode ser finalizada"""
        return self.status in [self.STATUS_IN_PROGRESS, self.STATUS_PAUSED]

    def can_assign_extraction(self):
        """Verifica se a extração pode ser atribuída"""
        return self.status == self.STATUS_PENDING

    # Métodos de transição de status
    def assign_extraction(self, assigned_to, assigned_by, notes=None):
        """Atribui a extração a um extrator"""
        if not self.can_assign_extraction():
            raise ValidationError("Extração não pode ser atribuída no status atual.")
        
        self.status = self.STATUS_ASSIGNED
        self.assigned_to = assigned_to
        self.assigned_by = assigned_by
        self.assigned_at = timezone.now()
        if notes:
            self.started_notes = notes
        self.save()
        
        # Atualiza o status do Case baseado nas extrações
        self.case_device.case.update_status_based_on_extractions()

    def start_extraction(self, user, notes=None):
        """Inicia a extração"""
        if not self.can_start_extraction():
            raise ValidationError("Extração não pode ser iniciada no status atual.")
        
        self.status = self.STATUS_IN_PROGRESS
        self.started_at = timezone.now()
        self.started_by = user
        if notes:
            self.started_notes = notes
        self.save()
        
        # Atualiza o status do Case baseado nas extrações
        self.case_device.case.update_status_based_on_extractions()

    def pause_extraction(self, user, notes=None):
        """Pausa a extração"""
        if not self.can_pause_extraction():
            raise ValidationError("Extração não pode ser pausada no status atual.")
        
        self.status = self.STATUS_PAUSED
        if notes:
            self.started_notes = notes
        self.save()
        
        # Atualiza o status do Case baseado nas extrações
        self.case_device.case.update_status_based_on_extractions()

    def complete_extraction(self, user, success=True, notes=None):
        """Finaliza a extração"""
        if not self.can_complete_extraction():
            raise ValidationError("Extração não pode ser finalizada no status atual.")
        
        self.status = self.STATUS_COMPLETED
        self.finished_at = timezone.now()
        self.finished_by = user
        self.extraction_result = success
        if notes:
            self.finished_notes = notes
        self.save()
        
        # Atualiza o status do Case baseado nas extrações
        self.case_device.case.update_status_based_on_extractions()
    
    # Propriedades calculadas
    @property
    def duration(self):
        """Duração total da extração"""
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return None

    @property
    def brute_force_duration(self):
        """Duração da força bruta"""
        if self.brute_force_started_at and self.brute_force_finished_at:
            return self.brute_force_finished_at - self.brute_force_started_at
        return None

    @property
    def is_extraction_successful(self):
        """Verifica se a extração foi bem-sucedida"""
        return self.extraction_result is True

    @property
    def requires_brute_force(self):
        """Verifica se requer força bruta"""
        return self.brute_force_started_at is not None
    
    def get_status_color(self):
        """Returns Bootstrap color class based on status"""
        status_colors = {
            self.STATUS_PENDING: 'warning',
            self.STATUS_ASSIGNED: 'info',
            self.STATUS_IN_PROGRESS: 'primary',
            self.STATUS_PAUSED: 'secondary',
            self.STATUS_COMPLETED: 'success',
        }
        return status_colors.get(self.status, 'secondary')
    
    def get_status_display(self):
        """Returns the status display"""
        status_map = {
            self.STATUS_PENDING: 'Aguardando Extrator',
            self.STATUS_ASSIGNED: 'Aguardando Início',
            self.STATUS_IN_PROGRESS: 'Em Andamento',
            self.STATUS_PAUSED: 'Pausado',
            self.STATUS_COMPLETED: 'Finalizada',
        }
        return status_map.get(self.status, self.status.title())
    