from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AuditedModel(models.Model):
    """
    Represents a base model with common attributes and methods for tracking object
    creation, updates, and soft deletion.

    This abstract model is intended to be inherited by other models to avoid code
    duplication and enforce consistent tracking of created, updated, and deleted
    object metadata. It also tracks object versioning for potential concurrency
    control.

    This model includes automatic validation of unique constraints that considers
    only non-deleted records (soft delete).

    Attributes:
        created_at (datetime): The timestamp when the instance was created.
        created_by (User): The user who created the instance.
        updated_at (datetime): The timestamp of the last modification.
        updated_by (User, optional): The user who last modified the instance.
        deleted_at (datetime): The timestamp when the instance was deleted.
        deleted_by (User, optional): The user who deleted the instance.
        version (int): The version of the instance.
    """

    created_at = models.DateTimeField(
        verbose_name=_('Criado em'),
        auto_now_add=True,
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Criado por'),
        related_name='%(class)s_created',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(
        verbose_name=_('Atualizado em'),
        auto_now=True,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Atualizado por'),
        related_name='%(class)s_updated',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    deleted_at = models.DateTimeField(
        verbose_name=_('Excluído em'),
        null=True,
        blank=True,
        default=None
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Excluído por'),
        related_name='%(class)s_deleted',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    version = models.IntegerField(_('Versão do Registro'), default=1)

    class Meta:
        abstract = True


class AbstractCaseModel(AuditedModel):
    """Abstract model for common case/request fields"""


    requester_agency_unit = models.ForeignKey(
        'base_tables.AgencyUnit',
        on_delete=models.PROTECT,
        related_name='%(class)s_requester_agency_units',
        null=True,
        blank=True,
        verbose_name=_('Unidade Solicitante'),
        help_text=_('Unidade solicitante')
    )

    requested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Solicitada em'),
        help_text=_('Data e hora da solicitação')
    )

    requested_device_amount = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        default=1,
        verbose_name=_('Quantidade de Dispositivos'),
        help_text=_('Quantidade de dispositivos solicitados')
    )

    extraction_unit = models.ForeignKey(
        'core.ExtractionUnit',
        on_delete=models.PROTECT,
        related_name='%(class)s_requested_extraction_units',
        null=True,
        blank=True,
        verbose_name=_('Unidade de Extração'),
        help_text=_('Unidade de extração')
    )

    requester_reply_email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name=_('E-mail de Resposta'),
        help_text=_('E-mail de resposta')
    )

    requester_authority_name = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name=_('Nome da Autoridade'),
        help_text=_('Nome completo da autoridade solicitante')
    )

    requester_authority_position = models.ForeignKey(
        'base_tables.EmployeePosition',
        on_delete=models.PROTECT,
        related_name='%(class)s_requester_authority_positions',
        null=True,
        blank=True,
        verbose_name=_('Cargo da Autoridade'),
        help_text=_('Cargo da autoridade solicitante')
    )

    request_procedures = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        verbose_name=_('Procedimentos'),
        help_text=_('Procedimentos (ex: IP, PJ, etc)')
    )
   
    crime_category = models.ForeignKey(
        'base_tables.CrimeCategory',
        on_delete=models.SET_NULL,
        related_name='%(class)s_crime_types',
        null=True,
        blank=True,
        verbose_name=_('Categoria de Crime'),
        help_text=_('Categoria de Crime')
    )    
    
    additional_info = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Informações Adicionais'),
        help_text=_('Informações adicionais')
    )

    class Meta:
        abstract = True

