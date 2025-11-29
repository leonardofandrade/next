from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.core.models import AuditedModel, AbstractCaseModel, ExtractionUnit
from apps.base_tables.models import ProcedureCategory
from apps.requisitions.models import ExtractionRequest


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