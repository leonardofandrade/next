from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import AuditedModel


class BaseTable(AuditedModel):
    """
    BaseTable model é a classe base para todas as tabelas basicas do sistema.
    Ele possui os campos:
    - name: Nome da tabela
    - acronym: Sigla da tabela
    - description: Descrição da tabela
    - created_at: Data de criação da tabela
    - created_by: Usuário que criou a tabela
    - updated_at: Data de atualização da tabela
    - updated_by: Usuário que atualizou a tabela
    - deleted_at: Data de exclusão da tabela
    - deleted_by: Usuário que excluiu a tabela
    - version: Versão da tabela
    """
    name = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        verbose_name='Nome')
    acronym = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        verbose_name='Sigla')
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descrição')
   
    class Meta:
        abstract = True
    def __str__(self):
        return f"{self.acronym} - {self.name}" \
            if self.acronym else self.name

class Organization(BaseTable):

    """
    Organization model representa o nível 1 da hierarquia de organizações de segurança pública e poder judiciário.
    Pode ter um nome e uma sigla.
    Pode ter uma descrição.
    """   

    class Meta:
        db_table = 'organization'
        unique_together = ('name', 'acronym')
        verbose_name = 'Instituição'
        verbose_name_plural = 'Instituições'
        # Note: MySQL performs case-insensitive string comparisons by default,
        # so we don't need a conditional unique constraint

class Agency(BaseTable):
    """
    Agency model represents an agency of an organization.
    It can have a parent agency, which is another agency of the same organization.
    """
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.DO_NOTHING,
        null=False,
        verbose_name='Organização',
    )

    class Meta:
        db_table = 'agency'
        verbose_name = 'Agência'
        verbose_name_plural = 'Agências'
        # Note: MySQL performs case-insensitive string comparisons by default
        unique_together = ['organization', 'name']

    def __str__(self):
        return f"{self.acronym} - {self.name}" \
            if self.acronym else self.name

class Department(BaseTable):
    """ 
    Department model represents a department of an agency.
    It can have a parent department, which is another department of the same agency.
    It can have a name and an acronym.
    It can have a description.
    """
    agency = models.ForeignKey(
        Agency,
        on_delete=models.DO_NOTHING,
        null=False,
        verbose_name='Agência',
    )
    parent_department = models.ForeignKey(
        'self',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        verbose_name='Departamento Pai'
    )
    
    class Meta:
        db_table = 'org_department'
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        # Note: MySQL performs case-insensitive string comparisons by default
        unique_together = ['agency', 'name']

    def __str__(self):
        return f"{self.acronym} - {self.name}" \
            if self.acronym else self.name
        
class AgencyUnit(BaseTable):
    """
    AgencyUnit model represents a unit of an agency.
    It can have a parent unit, which is another unit of the same agency.
    """
    agency = models.ForeignKey(
        Agency,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='Agência'
    )
   
    # Contact Information
    phone_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default='',
        verbose_name='Telefone'
    )
    secondary_phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default='',
        verbose_name='Telefone Secundário'
    )
    primary_email = models.EmailField(
        max_length=254,
        null=True,
        blank=True,
        default='',
        verbose_name='E-mail Funcional'
    )
    # Address Information
    address_line_1 = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        default='',
        verbose_name='Endereço'
    )
    address_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default='',
        verbose_name='Número'
    )
    address_line_2 = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default='',
        verbose_name='Complemento'
    )
    neighborhood = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default='',
        verbose_name='Bairro'
    )
    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default='',
        verbose_name='Cidade'
    )
    state = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default='CE',
        verbose_name='Estado'
    )
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default='Brasil',
        verbose_name='País'
    )
    address_postal_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        default='',
        verbose_name='CEP'
    )
    

    def __str__(self):
        if self.agency and self.acronym:
            return f"{self.agency.acronym} - {self.acronym}"
        elif self.agency:
            return f"{self.agency.acronym} - {self.name}"
        elif self.acronym:
            return self.acronym
        else:
            return self.name

    class Meta:
        db_table = 'org_agency_unit'
        verbose_name = 'Unidade Operacional'
        verbose_name_plural = 'Unidades Operacionais'
        # Note: MySQL performs case-insensitive string comparisons by default
        unique_together = ['agency', 'name']

class EmployeePosition(BaseTable):
    """
    EmployeePosition model represents a position of an employee.
    It can have a name and an acronym.
    It can have a description.
    """
    # indicas que ele deve vir primeiro na lista de cargos
    default_selection = models.BooleanField(
        default=False,
        verbose_name='Seleção Padrão',
        help_text='Se selecionado, este cargo será exibido primeiro na lista de cargos'
    )

    class Meta:
        db_table = 'org_employee_position'
        unique_together = ['name', 'acronym']
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        # Note: MySQL performs case-insensitive string comparisons by default
        ordering = ['-default_selection', 'name']

    def __str__(self):
        return f"{self.name}"

class ProcedureCategory(BaseTable):
    """
    ProcedureCategory model represents a category of a procedure.
    It can have a name and an acronym.
    It can have a description.
    """
    default_selection = models.BooleanField(
        default=False,
        verbose_name='Seleção Padrão',
        help_text='Se selecionado, esta categoria de procedimento será exibida primeiro na lista de categorias de procedimentos'
    )

    class Meta:
        db_table = 'procedure_category'
        unique_together = ['name', 'acronym']
        verbose_name = 'Categoria de Procedimento'
        verbose_name_plural = 'Categorias de Procedimento'
        # Note: MySQL performs case-insensitive string comparisons by default
        ordering = ['-default_selection', 'name']

    def __str__(self):
        return f"{self.acronym} - {self.name}" \
            if self.acronym else self.name

class CrimeCategory(BaseTable):
    """
    CrimeCategory model represents a category of crime.
    It can have a name and an acronym.
    It can have a description.
    """
    default_selection = models.BooleanField(
        default=False,
        verbose_name='Seleção Padrão',
        help_text='Se selecionado, esta categoria de crime será exibida primeiro na lista de categorias de crimes'
    )

    class Meta:
        db_table = 'crime_category'
        unique_together = ['name', 'acronym']
        verbose_name = 'Categoria de Crime'
        verbose_name_plural = 'Categorias de Crimes'
        # Note: MySQL performs case-insensitive string comparisons by default
        ordering = ['-default_selection', 'name']

    def __str__(self):
        return self.name

class DeviceCategory(BaseTable):
    """
    DeviceCategory model represents a category of a device.
    It can have a name and an acronym.
    It can have a description.
    """
    default_selection = models.BooleanField(
        default=False,
        verbose_name='Seleção Padrão',
        help_text='Se selecionado, esta categoria de dispositivo será exibida primeira na lista de categorias de dispositivos'
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False,
        verbose_name='Nome'
    )

    class Meta:
        db_table = 'device_category'
        verbose_name = 'Categoria de Dispositivo'
        verbose_name_plural = 'Categorias de Dispositivo'
        ordering = ['-default_selection', 'name']

    def __str__(self):
        return self.name

class DeviceBrand(BaseTable):
    """
    DeviceBrand model represents a brand of a device.
    It can have a name and an acronym.
    It can have a description.
    """

    class Meta:
        db_table = 'device_brand'
        verbose_name = _('Marca')
        verbose_name_plural = _('Marcas')
        ordering = ['name']

class DeviceModel(AuditedModel):
    brand = models.ForeignKey(
        DeviceBrand,
        null=False,
        verbose_name=_('Modelo'),
        related_name='dev_model',
        on_delete=models.PROTECT
    )
    name = models.CharField(
        _('Nome'),
        max_length=100,
        null=False
    )
    commercial_name = models.CharField(
        _('Nome Comercial'),
        max_length=100,
        null=True,
        blank=True
    )
    code = models.CharField(
        _('Código do Modelo'),
        max_length=50,
        blank=True,
        null=True
    )
    description = models.TextField(_('Descrição'), blank=True)

    class Meta:
        db_table = 'device_model'
        unique_together = ['brand', 'name']
        verbose_name = _('Modelo de Dispositivo')
        verbose_name_plural = _('Modelos de Dispositivo')

    def __str__(self):
        return f"{self.brand} - {self.name}"

class DocumentCategory(BaseTable):
    """
    DocumentCategory model represents a category of a document.
    It can have a name and an acronym.
    It can have a description.
    """
    default_selection = models.BooleanField(
        default=False,
        verbose_name='Seleção Padrão',
        help_text='Se selecionado, esta categoria de documento será exibida primeiro na lista de categorias de documentos'
    )

    class Meta:
        db_table = 'document_category'
        unique_together = ['name', 'acronym']
        verbose_name = 'Categoria de Documento'
        verbose_name_plural = 'Categorias de Documentos'
        # Note: MySQL performs case-insensitive string comparisons by default
        ordering = ['-default_selection', 'name']

    def __str__(self):
        return f"{self.acronym} - {self.name}" \
            if self.acronym else self.name
