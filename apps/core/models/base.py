from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.middleware import get_current_user


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

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para preencher automaticamente
        os campos created_by e updated_by usando o usuário atual do contexto.
        """
        current_user = get_current_user()
        
        # Se é uma nova instância (ainda não tem PK)
        if not self.pk:
            # Preenche created_by se ainda não estiver preenchido e houver usuário atual
            if current_user and not self.created_by:
                self.created_by = current_user
        
        # Sempre atualiza updated_by se houver usuário atual
        if current_user:
            self.updated_by = current_user
        
        super().save(*args, **kwargs)

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


class AbstractDeviceModel(AuditedModel):
    """Abstract model for Device Models"""
        
    """ Device information """
    device_category = models.ForeignKey(
        'base_tables.DeviceCategory',
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name='devices',
        verbose_name=_('Categoria'),
        help_text=_('Categoria do dispositivo')
    )
    device_model = models.ForeignKey(
        'base_tables.DeviceModel',
        null=True,
        verbose_name=_('Modelo'),
        related_name='devices',
        on_delete=models.PROTECT
    )
    color = models.CharField(
        _('Cor'),
        null=True,
        max_length=50, blank=True
    )

    is_imei_unknown = models.BooleanField(
        _('IMEI Desconhecido'),
        null=True,
        blank=True,
    )

    imei_01 = models.CharField(
        _('IMEI 01'),
        null=True,
        max_length=50, 
        blank=True)
    imei_02 = models.CharField(
        _('IMEI 02'),
        null=True,
        max_length=50, 
        blank=True)
    imei_03 = models.CharField(
        _('IMEI 03'),
        null=True,
        max_length=50, 
        blank=True)
    imei_04 = models.CharField(
        _('IMEI 04'),
        null=True,
        max_length=50, 
        blank=True)
    imei_05 = models.CharField(
        _('IMEI 05'),
        null=True,
        max_length=50, 
        blank=True)

    owner_name = models.CharField(
        _('Nome do Proprietário'),
        null=True,
        max_length=200,
        help_text=_('Nome do Proprietário'),
    )

    internal_storage = models.PositiveIntegerField(
        _('Armazenamento Interno (GB)'),
        null=True,
        blank=True,
        help_text=_('Capacidade de armazenamento interna do dispositivo em GB (ex: iPhone 512GB)')
    )

    """ Device status information """
    is_turned_on = models.BooleanField(
        _('Ligado'),
        null=True,
        blank=True,
    )
    is_locked = models.BooleanField(
        _('Bloqueado'),
        null=True,
        blank=True,
    )

    """ Device password information """
    is_password_known = models.BooleanField(
        _('Senha Conhecida'),
        null=True,
        blank=True,
    )
    PASSWORD_CHOICES = (
        ('pin', 'PIN'),
        ('password', 'Senha'),
        ('pattern', 'Padrão'),
        ('bio', 'Biometria'),
        ('none', 'Nenhum'),
    )
    password_type = models.CharField(
        _('Tipo de Senha'),
        null=True,
        blank=True,
        max_length=20,
        choices=PASSWORD_CHOICES,
        help_text=_('Tipo')
    )
    password = models.CharField(
        _('Senha'),
        max_length=100,
        null=True,
        blank=True,
        help_text=_('Senha')
    )
    """ Device physical condition information """
    is_damaged = models.BooleanField(
        _('Danificado'),
        null=True,
        blank=True,
    )
    damage_description = models.CharField(
        _('Descrição dos danos'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Descrição dos danos')
    )
    has_fluids = models.BooleanField(
        _('Presença de Fluidos'),
        null=True,
        blank=True,
        help_text=_('Indica se há presença de fluidos no dispositivo')
    )
    fluids_description = models.CharField(
        _('Descrição dos flúidos'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Descreva os fluidos. Ex.: sangue, água, óleo, etc.')
    )
    """ Device accessories information """
    has_sim_card = models.BooleanField(
        _('Chip SIM'),
        null=True,
        blank=True,
        help_text=_('Indica se há presença de chip SIM no dispositivo')
    )
    sim_card_info = models.CharField(
        _('Informações do Chip'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Informações sobre o chip, se houver')
    )

    has_memory_card = models.BooleanField(
        _('Cartão de Memória'),
        null=True,
        blank=True,
        help_text=_('Indica se há presença de cartão de memória no dispositivo')
    )
    memory_card_info = models.CharField(
        _('Informações do Cartão de Memória'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Informações sobre o cartão de memória, se houver')
    )
    has_other_accessories = models.BooleanField(
        _('Outros Acessórios'),
        null=True,
        blank=True,
        help_text=_('Indica se há presença de outros acessórios no dispositivo')
    )
    other_accessories_info = models.CharField(
        _('Informações dos Outros Acessórios'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Ex.: Capa, Carregador, etc.')
    )

    """ Device security information """
    is_sealed = models.BooleanField(
        _('Lacrado'),
        null=True,
        blank=True,
    )
    security_seal = models.CharField(
        _('Número do Lacre'),
        max_length=100,
        null=True,
        blank=True,
        help_text=_('Número do lacre')
    )

    additional_info = models.TextField(
        _('Informações Adicionais'),
        null=True,
        blank=True,
        help_text=_('Informações adicionais sobre o dispositivo')
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.device_model}" if self.device_model else f"{self.type}"

    def get_device_imei_as_list(self):
        """
        Retorna o IMEI do dispositivo como uma string.
        """
        imei_list = []
        if not self.imei_01 and not self.imei_02 and not self.imei_03 and not self.imei_04 and not self.imei_05:
            return "IMEI Não Informado"
        else:
            if self.imei_01:
                imei_list.append(self.imei_01)
            if self.imei_02:
                imei_list.append(self.imei_02)
            if self.imei_03:
                imei_list.append(self.imei_03)
            if self.imei_04:
                imei_list.append(self.imei_04)
            if self.imei_05:
                imei_list.append(self.imei_05)
        
        return ", ".join(imei_list)