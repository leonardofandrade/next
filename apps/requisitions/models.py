from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from apps.core.models import AbstractCaseModel

class ExtractionRequest(AbstractCaseModel):
    """ Model for Data Extractions Requests """

    REQUEST_STATUS_PENDING = 'pending'
    REQUEST_STATUS_ASSIGNED = 'assigned'
    REQUEST_STATUS_RECEIVED = 'received'
    REQUEST_STATUS_WAITING_START = 'waiting_start'
    REQUEST_STATUS_IN_PROGRESS = 'in_progress'
    REQUEST_STATUS_WAITING_COLLECT = 'waiting_collection'

    REQUEST_STATUS_CHOICES = [
        (REQUEST_STATUS_PENDING, 'Pendente'),
        (REQUEST_STATUS_ASSIGNED, 'Aguardando Material'),
        (REQUEST_STATUS_RECEIVED, 'Material Recebido'),
        (REQUEST_STATUS_WAITING_START, 'Aguardando Início'),
        (REQUEST_STATUS_IN_PROGRESS, 'Em Andamento'),
        (REQUEST_STATUS_WAITING_COLLECT, 'Aguardando Coleta'),
    ]   
    status = models.CharField(
        max_length=50,
        choices=REQUEST_STATUS_CHOICES,
        default=REQUEST_STATUS_ASSIGNED,
        verbose_name=_('Status'),
        help_text=_("Status da solicitação de extração.")
    )
    ## 
    # Campos para o processo de recebimento do material. 
    # received_at e received_by são obrigatórios serão preenchidos automaticamente quando o material for recebido.
    # received_notes é opcional e será preenchido pelo usuário que recebeu o material.
   
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Recebido em'),
        help_text=_('Data e hora do recebimento do material')
    )
    received_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Recebido por'),
        help_text=_('Usuário que recebeu o material')
    )
    receipt_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Observações'),
        help_text=_('Observações sobre o recebimento do material')
    )
    
    # is_legacy é um flag para indicar se a solicitação de extração é legada.
    # spreadsheet_line é a linha do arquivo de planilha que contém a solicitação de extração.
    is_legacy = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_('É legado'),
        help_text=_('Indica se a solicitação de extração é legada')
    )
    spreadsheet_line = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Linha do arquivo de planilha'),
        help_text=_('Linha do arquivo de planilha')
    )

    class Meta:
        db_table = 'extraction_request'
        verbose_name = _('Solicitação de Extração')
        verbose_name_plural = _('Solicitações de Extração')

    def __str__(self):
        return f"{self.requester_agency_unit.name if self.requester_agency_unit else 'N/A'} - {self.requested_at}"
    
    def get_status_color(self):
        """Returns Bootstrap color class based on status"""
        status_colors = {
            self.REQUEST_STATUS_PENDING: 'secondary',
            self.REQUEST_STATUS_ASSIGNED: 'warning',
            self.REQUEST_STATUS_RECEIVED: 'info',
            self.REQUEST_STATUS_WAITING_START: 'success',
            self.REQUEST_STATUS_IN_PROGRESS: 'success',
            self.REQUEST_STATUS_WAITING_COLLECT: 'primary',
        }
        return status_colors.get(self.status, 'secondary')
    
    def get_status_display(self):
        """Returns human-readable status display"""
        status_map = {
            self.REQUEST_STATUS_PENDING: 'Pendente',
            self.REQUEST_STATUS_ASSIGNED: 'Aguardando Material',
            self.REQUEST_STATUS_RECEIVED: 'Material Recebido',
            self.REQUEST_STATUS_WAITING_START: 'Aguardando Início',
            self.REQUEST_STATUS_IN_PROGRESS: 'Em Andamento',
            self.REQUEST_STATUS_WAITING_COLLECT: 'Aguardando Coleta',
        }
        return status_map.get(self.status, self.status)
    