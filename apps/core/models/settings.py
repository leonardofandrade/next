from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .base import AuditedModel
from django.utils.translation import gettext_lazy as _
from .extraction_agency import ExtractionAgency



class GeneralSettings(AuditedModel):
    """
    Modelo para configurações gerais da aplicação.
    """
    
    # Referência à Agência
    extraction_agency = models.OneToOneField(
        ExtractionAgency,
        on_delete=models.PROTECT,
        verbose_name=_('Agência Central'),
        help_text=_('Agência na qual o sistema está instalado'),
        null=True,
        blank=True
    )
    
    # Configurações do Sistema
    system_name = models.CharField(
        max_length=100,
        verbose_name=_('Nome do Sistema'),
        help_text=_('Nome da aplicação/sistema'),
        blank=True,
        default=None,
        null=True,
    )
    
    system_version = models.CharField(
        max_length=20,
        verbose_name=_('Versão do Sistema'),
        help_text=_('Versão atual do sistema'),
        blank=True,
        default=None,
        null=True,
    )
    
    system_description = models.TextField(
        verbose_name=_('Descrição do Sistema'),
        help_text=_('Descrição breve do sistema'),
        blank=True,
        default=None,
        null=True,
    )
    
    # Configurações de Interface
    primary_color = models.CharField(
        max_length=7,
        verbose_name=_('Cor Primária'),
        help_text=_('Cor primária do sistema (formato hex: #000000)'),
        blank=True,
        default=None,
        null=True,
    )
    
    secondary_color = models.CharField(
        max_length=7,
        verbose_name=_('Cor Secundária'),
        help_text=_('Cor secundária do sistema (formato hex: #000000)'),
        blank=True,
        default=None,
        null=True,
    )
    
    # Configurações de Funcionamento
    maintenance_mode = models.BooleanField(
        verbose_name=_('Modo de Manutenção'),
        help_text=_('Ativar modo de manutenção (bloqueia acesso de usuários)'),
        null=True,
        default=False,
    )
    
    maintenance_message = models.TextField(
        verbose_name=_('Mensagem de Manutenção'),
        help_text=_('Mensagem exibida durante o modo de manutenção'),
        blank=True,
        null=True,
        default='Sistema em manutenção. Tente novamente mais tarde.'
    )
    
    # Configurações de Backup
    backup_enabled = models.BooleanField(
        verbose_name=_('Backup Automático'),
        help_text=_('Ativar backup automático do sistema'),
        default=False
    )
    
    backup_frequency = models.CharField(
        max_length=20,
        verbose_name=_('Frequência do Backup'),
        help_text=_('Frequência do backup (daily, weekly, monthly)'),
        choices=[
            ('daily', _('Diário')),
            ('weekly', _('Semanal')),
            ('monthly', _('Mensal')),
        ],
        default='daily'
    )
    
    class Meta:
        db_table = 'cfg_general'
        verbose_name = _('Configurações Gerais')
        verbose_name_plural = _('Configurações Gerais')
        
class EmailSettings(AuditedModel):
    """
    Modelo para configurações de e-mail da aplicação.
    """
    
    # Referência à Agência
    extraction_agency = models.OneToOneField(
        ExtractionAgency,
        on_delete=models.PROTECT,
        verbose_name=_('Agência'),
        help_text=_('Agência na qual o sistema está instalado'),
        null=True,
        blank=True
    )
    
    email_host = models.CharField(
        max_length=100,
        verbose_name=_('Servidor SMTP'),
        help_text=_('Servidor de e-mail para envio (ex: smtp.gmail.com)'),
        default='localhost'
    )
    email_port = models.IntegerField(
        verbose_name=_('Porta SMTP'),
        help_text=_('Porta do servidor de e-mail'),
        default=587
    )
    
    
    email_use_tls = models.BooleanField(
        verbose_name=_('Usar TLS'),
        help_text=_('Usar conexão segura TLS'),
        default=True
    )
    
    email_use_ssl = models.BooleanField(
        verbose_name=_('Usar SSL'),
        help_text=_('Usar conexão segura SSL'),
        default=False
    )
    
    email_host_user = models.EmailField(
        verbose_name=_('Usuário do E-mail'),
        help_text=_('E-mail para autenticação no servidor SMTP'),
        blank=True,
        default=''
    )
    
    email_host_password = models.CharField(
        max_length=100,
        verbose_name=_('Senha do E-mail'),
        help_text=_('Senha para autenticação no servidor SMTP'),
        blank=True,
        default=''
    )
    
    email_from_name = models.CharField(
        max_length=100,
        verbose_name=_('Nome do Remetente'),
        help_text=_('Nome que aparece como remetente dos e-mails'),
        default='Sistema'
    )
    
    class Meta:
        db_table = 'cfg_email'
        verbose_name = _('Configurações de E-mail')
        verbose_name_plural = _('Configurações de E-mail')


class ReportsSettings(AuditedModel):
    """
    Modelo para configurações de relatórios da aplicação.
    """
    
    # Referência à Agência
    extraction_agency = models.OneToOneField(
        ExtractionAgency,
        on_delete=models.PROTECT,
        verbose_name=_('Agência'),
        help_text=_('Agência na qual o sistema está instalado'),
        null=True,
        blank=True
    )
    
    # Configurações de Relatórios
    reports_enabled = models.BooleanField(
        verbose_name=_('Relatórios Ativados'),
        help_text=_('Ativar relatórios da aplicação'),
        default=True
    )

    default_report_header_logo = models.BinaryField(
        verbose_name=_('Logo do Relatório'),
        help_text=_('Logo do relatório (formato binário)'),
        blank=True,
        null=True
    )
    secondary_report_header_logo = models.BinaryField(
        verbose_name=_('Logo Secundária do Relatório'),
        help_text=_('Logo secundária do relatório (formato binário)'),
        blank=True,
        null=True
    )

    distribution_report_notes = models.TextField(
        verbose_name=_('Nota do Relatório de Distribuição'),
        help_text=_('Nota do relatório de distribuição'),
        blank=True,
        null=True
    )

    report_cover_header_line_1 = models.CharField(
        max_length=100,
        verbose_name=_('Linha 1 do Cabeçalho do Relatório'),
        help_text=_('Linha 1 do cabeçalho do relatório'),
        blank=True,
        null=True
    )
    report_cover_header_line_2 = models.CharField(
        max_length=100,
        verbose_name=_('Linha 2 do Cabeçalho do Relatório'),
        help_text=_('Linha 2 do cabeçalho do relatório'),
        blank=True,
        null=True
    )
    report_cover_header_line_3 = models.CharField(
        max_length=100,
        verbose_name=_('Linha 3 do Cabeçalho do Relatório'),
        help_text=_('Linha 3 do cabeçalho do relatório'),
        blank=True,
        null=True
    )
    report_cover_footer_line_1= models.CharField(
        max_length=100,
        verbose_name=_('Linha 1 do Rodapé do Relatório'),
        help_text=_('Linha 1 do rodapé do relatório'),
        blank=True,
        null=True
    )
    report_cover_footer_line_2 = models.CharField(
        max_length=100,
        verbose_name=_('Linha 2 do Rodapé do Relatório'),
        help_text=_('Linha 2 do rodapé do relatório'),
        blank=True,
        null=True
    )
    
    def get_default_logo_base64(self):
        """
        Retorna o logo padrão em formato base64 para exibição em templates.
        """
        if self.default_report_header_logo:
            import base64
            return base64.b64encode(self.default_report_header_logo).decode('utf-8')
        return None
    
    def get_secondary_logo_base64(self):
        """
        Retorna o logo secundário em formato base64 para exibição em templates.
        """
        if self.secondary_report_header_logo:
            import base64
            return base64.b64encode(self.secondary_report_header_logo).decode('utf-8')
        return None
    
    class Meta:
        db_table = 'cfg_reports'
        verbose_name = _('Configurações de Relatórios')
        verbose_name_plural = _('Configurações de Relatórios')