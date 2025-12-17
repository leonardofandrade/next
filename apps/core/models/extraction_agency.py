from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .base import AuditedModel
import base64

class ExtractionAgency(AuditedModel):
    """
    Modelo para a agência central de extração de dados. A agência central é a agência que gerencia as unidades de extração de dados.
    Representa a agência central que gerencia as unidades de extração de dados.
    À principio  só poderá existir uma agência central.
    """

    acronym = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Sigla'),
        help_text=_('Sigla da agência de extração de dados'),
    )

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Nome'),
        help_text=_('Nome da agência de extração de dados'),
    )
    
    ## Campos para responsável
    incharge_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Nome do Responsável'),
        help_text=_('Nome do responsável pela agência de extração'),
    )
    
    incharge_position = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Cargo do Responsável'),
        help_text=_('Cargo do responsável pela agência de extração'),
    )
    
    ## Logo principal (armazenado no banco de dados)
    main_logo = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_('Logo Principal'),
        help_text=_('Logo principal da agência de extração armazenado no banco de dados')
    )

    class Meta:
        db_table = 'extr_agency'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]
        verbose_name = _('Agência de Extração de Dados')
        verbose_name_plural = _('Agências de Extração de Dados')
        unique_together = ['acronym', 'name']

    def __str__(self):
        """Retorna uma representação legível da agência de extração de dados."""
        return self.acronym if self.acronym else self.name
    
    @property
    def has_main_logo(self):
        """Verifica se a agência tem um logo"""
        return self.main_logo is not None and bool(self.main_logo)
    
    @property
    def get_main_logo_base64(self):
        """Retorna o logo em base64 para exibição"""
        if self.main_logo:
            try:
                return base64.b64encode(self.main_logo).decode('utf-8')
            except Exception:
                return None
        return None
    
    @property
    def get_main_logo_mime_type(self):
        """Detecta o tipo MIME da imagem baseado nos primeiros bytes"""
        if not self.main_logo:
            return 'image/png'  # Default
        
        try:
            # Verifica os primeiros bytes para detectar o formato
            header = self.main_logo[:8] if len(self.main_logo) >= 8 else self.main_logo
            
            # PNG: 89 50 4E 47 0D 0A 1A 0A
            if header[:8] == b'\x89PNG\r\n\x1a\n':
                return 'image/png'
            # JPEG: FF D8 FF
            elif header[:3] == b'\xff\xd8\xff':
                return 'image/jpeg'
            # GIF: 47 49 46 38
            elif header[:4] == b'GIF8':
                return 'image/gif'
            # WebP: RIFF...WEBP
            elif header[:4] == b'RIFF' and len(self.main_logo) > 8 and self.main_logo[8:12] == b'WEBP':
                return 'image/webp'
            else:
                return 'image/png'  # Default
        except Exception:
            return 'image/png'  # Default em caso de erro

class ExtractionUnit(AuditedModel):
    """
    Modelo para unidades de extração de dados.
    """

    agency = models.ForeignKey(
        ExtractionAgency,
        on_delete=models.PROTECT,
        related_name='extraction_units',
        verbose_name=_('Agência Central'),
        help_text=_('Agência Central'),
    )
    acronym = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Sigla'),
        help_text=_('Sigla da unidade de extração'),
    )
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Nome'),
        help_text=_('Nome da unidade de extração'),
    )
    ## Campos para contato
    primary_phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Telefone Principal'),
        help_text=_('Telefone principal da unidade de extração'),
    )
    secondary_phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Telefone Secundário'),
        help_text=_('Telefone secundário da unidade de extração'),
    )
    primary_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Email Principal'),
        help_text=_('Email principal da unidade de extração'),
    )
    secondary_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Email Secundário'),
        help_text=_('Email secundário da unidade de extração'),
    )
    ## Campos para endereço
    address_line1 = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Endereço'),
        help_text=_('Endereço da unidade de extração'),
    )
    address_number = models.CharField(
        max_length=255, 
        null=True,
        blank=True,
        verbose_name=_('Número'),
        help_text=_('Número do endereço da unidade de extração'),
    )
    address_line2 = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Endereço'),
        help_text=_('Endereço da unidade de extração'),
    )
    neighborhood = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Bairro'),
        help_text=_('Bairro da unidade de extração'),
    )
    city_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Cidade'),
        help_text=_('Cidade da unidade de extração'),
    )
    postal_code = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('CEP'),
        help_text=_('CEP da unidade de extração'),
    )
    state_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Estado'),
        help_text=_('Estado da unidade de extração'),
    )
    country_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('País'),
        help_text=_('País da unidade de extração'),
    )
    ## Campos para responsável
    incharge_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Nome do Responsável'),
        help_text=_('Nome do responsável pela unidade de extração'),
    )
    incharge_position = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Cargo do Responsável'),
        help_text=_('Cargo do responsável pela unidade de extração'),
    )
    ## Campos para email de resposta
    reply_email_template = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Template de email de resposta'),
        help_text=_('Template de email de resposta para o solicitante'),
    )
    reply_email_subject = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Assunto do email de resposta'),
        help_text=_('Assunto do email de resposta para o solicitante'),
    )

    class Meta:
        db_table = 'extr_unit'
        verbose_name = _('Unidade de Extração')
        verbose_name_plural = _('Unidades de Extração')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['acronym']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        """Retorna uma representação legível da unidade de extração."""
        return self.acronym if self.acronym else self.name

class ExtractionUnitSettings(AuditedModel):
    """
    Modelo para configurações de uma unidade de extração.
    """
    extraction_unit = models.OneToOneField(
        ExtractionUnit,
        on_delete=models.PROTECT,
        related_name='extraction_unit_settings',
    )

    reply_email_template = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Template de email de resposta'),
        help_text=_('Template de email de resposta para o solicitante'),
    )
    reply_email_subject = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Assunto do email de resposta'),
        help_text=_('Assunto do email de resposta para o solicitante'),
    )


    class Meta:
        db_table = 'extr_unit_settings'
        verbose_name = _('Configuração de Unidade de Extração')
        verbose_name_plural = _('Configurações de Unidades de Extração')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        """Retorna uma representação legível da configuração da unidade de extração."""
        return f"{self.extraction_unit.acronym} - Configurações"


class ExtractionUnitReportSettings(AuditedModel):
    """
    Modelo para configurações de relatórios de uma unidade de extração.
    """
    extraction_unit = models.OneToOneField(
        ExtractionUnit,
        on_delete=models.PROTECT,
        related_name='report_settings',
        verbose_name=_('Unidade de Extração'),
    )

    # Configurações de Relatórios
    reports_enabled = models.BooleanField(
        verbose_name=_('Relatórios Ativados'),
        help_text=_('Ativar relatórios para esta unidade'),
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
    report_cover_footer_line_1 = models.CharField(
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

    class Meta:
        db_table = 'extr_unit_report_settings'
        verbose_name = _('Configuração de Relatórios da Unidade')
        verbose_name_plural = _('Configurações de Relatórios das Unidades')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        """Retorna uma representação legível da configuração."""
        return f"{self.extraction_unit.acronym} - Configurações de Relatórios"

    def get_default_logo_base64(self):
        """Retorna o logo padrão em formato base64 para exibição em templates."""
        if self.default_report_header_logo:
            return base64.b64encode(self.default_report_header_logo).decode('utf-8')
        return None

    def get_secondary_logo_base64(self):
        """Retorna o logo secundário em formato base64 para exibição em templates."""
        if self.secondary_report_header_logo:
            return base64.b64encode(self.secondary_report_header_logo).decode('utf-8')
        return None


class DispatchSequenceNumber(AuditedModel):
    """
    Modelo para controlar a numeração sequencial de ofícios de resposta por extraction unit e ano.
    """
    extraction_unit = models.ForeignKey(
        ExtractionUnit,
        on_delete=models.PROTECT,
        related_name='dispatch_sequence_numbers',
        verbose_name=_('Unidade de Extração'),
        help_text=_('Unidade de extração'),
    )
    year = models.IntegerField(
        null=False,
        blank=False,
        verbose_name=_('Ano'),
        help_text=_('Ano para controle da numeração sequencial'),
    )
    last_number = models.IntegerField(
        default=0,
        verbose_name=_('Último Número'),
        help_text=_('Último número de ofício gerado para esta unidade e ano'),
    )

    class Meta:
        db_table = 'dispatch_sequence_number'
        verbose_name = _('Numeração Sequencial de Ofício')
        verbose_name_plural = _('Numerações Sequenciais de Ofícios')
        unique_together = [['extraction_unit', 'year']]
        ordering = ['-year', '-last_number']
        indexes = [
            models.Index(fields=['extraction_unit', 'year']),
        ]

    def __str__(self):
        """Retorna uma representação legível da numeração sequencial."""
        return f"{self.extraction_unit.acronym} - {self.year} - Último: {self.last_number}"

    @classmethod
    def get_next_number(cls, extraction_unit, year):
        """Obtém o próximo número sequencial para uma extraction unit e ano."""
        sequence, created = cls.objects.get_or_create(
            extraction_unit=extraction_unit,
            year=year,
            defaults={'last_number': 0}
        )
        sequence.last_number += 1
        sequence.save()
        return sequence.last_number


class DocumentTemplate(AuditedModel):
    """
    Modelo para armazenar templates de documentos por extraction unit.
    """
    extraction_unit = models.ForeignKey(
        ExtractionUnit,
        on_delete=models.PROTECT,
        related_name='document_templates',
        verbose_name=_('Unidade de Extração'),
        help_text=_('Unidade de extração'),
    )
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_('Nome do Template'),
        help_text=_('Nome identificador do template'),
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Descrição'),
        help_text=_('Descrição do template'),
    )
    # Campos para logo do cabeçalho

    header_left_logo = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_('Logo do Cabeçalho Esquerdo'),
        help_text=_('Logo do cabeçalho esquerdo do template'),
    )
    header_right_logo = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_('Logo do Cabeçalho Direito'),
        help_text=_('Logo do cabeçalho direito do template'),
    )
    header_text = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Texto do Cabeçalho'),
        help_text=_('Texto do cabeçalho do template'),
    )

    # Campos para texto do corpo

    subject_text = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Texto do Assunto'),
        help_text=_('Texto do assunto do template'),
    )
    
    body_text = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Texto do Corpo do Template'),
        help_text=_('Texto do corpo do template'),
    )

    signature_text = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Texto da Assinatura'),
        help_text=_('Texto da assinatura do template'),
    )

    watermark_text = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Texto da Água-Marinha'),
        help_text=_('Texto da água-marinha do template'),
    )
    watermark_logo = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_('Logo da Água-Marinha'),
        help_text=_('Logo da água-marinha do template'),
    )

    # Campos para logo do rodapé
    footer_left_logo = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_('Logo do Rodapé Esquerdo'),
        help_text=_('Logo do rodapé esquerdo do template'),
    )
    footer_right_logo = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_('Logo do Rodapé Direito'),
        help_text=_('Logo do rodapé direito do template'),
    )
    footer_text = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Texto do Rodapé'),
        help_text=_('Texto do rodapé do template'),
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Padrão'),
        help_text=_('Indica se este é o template padrão para a unidade'),
    )


    class Meta:
        db_table = 'document_template'
        verbose_name = _('Template de Documento')
        verbose_name_plural = _('Templates de Documentos')
        ordering = ['-is_default', 'name']
        indexes = [
            models.Index(fields=['extraction_unit', 'is_default']),
        ]

    def __str__(self):
        """Retorna uma representação legível do template."""
        return f"{self.extraction_unit.acronym} - {self.name}"

    def save(self, *args, **kwargs):
        """Garante que apenas um template padrão existe por extraction unit."""
        if self.is_default:
            # Desativa outros templates padrão da mesma unidade
            DocumentTemplate.objects.filter(
                extraction_unit=self.extraction_unit,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    # Helpers para exibir logos (base64) nos templates
    @staticmethod
    def _image_to_base64(image_bytes: bytes):
        if not image_bytes:
            return None
        try:
            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception:
            return None

    @staticmethod
    def _detect_image_mime_type(image_bytes: bytes) -> str:
        if not image_bytes:
            return 'image/png'
        try:
            header = image_bytes[:12] if len(image_bytes) >= 12 else image_bytes
            # PNG
            if header[:8] == b'\x89PNG\r\n\x1a\n':
                return 'image/png'
            # JPEG
            if header[:3] == b'\xff\xd8\xff':
                return 'image/jpeg'
            # GIF
            if header[:4] == b'GIF8':
                return 'image/gif'
            # WebP: RIFF....WEBP
            if header[:4] == b'RIFF' and len(image_bytes) > 12 and image_bytes[8:12] == b'WEBP':
                return 'image/webp'
        except Exception:
            pass
        return 'image/png'

    @property
    def has_header_left_logo(self):
        return self.header_left_logo is not None and bool(self.header_left_logo)

    @property
    def get_header_left_logo_base64(self):
        return self._image_to_base64(self.header_left_logo)

    @property
    def get_header_left_logo_mime_type(self):
        return self._detect_image_mime_type(self.header_left_logo)

    @property
    def has_header_right_logo(self):
        return self.header_right_logo is not None and bool(self.header_right_logo)

    @property
    def get_header_right_logo_base64(self):
        return self._image_to_base64(self.header_right_logo)

    @property
    def get_header_right_logo_mime_type(self):
        return self._detect_image_mime_type(self.header_right_logo)

    @property
    def has_footer_left_logo(self):
        return self.footer_left_logo is not None and bool(self.footer_left_logo)

    @property
    def get_footer_left_logo_base64(self):
        return self._image_to_base64(self.footer_left_logo)

    @property
    def get_footer_left_logo_mime_type(self):
        return self._detect_image_mime_type(self.footer_left_logo)

    @property
    def has_footer_right_logo(self):
        return self.footer_right_logo is not None and bool(self.footer_right_logo)

    @property
    def get_footer_right_logo_base64(self):
        return self._image_to_base64(self.footer_right_logo)

    @property
    def get_footer_right_logo_mime_type(self):
        return self._detect_image_mime_type(self.footer_right_logo)

    @property
    def has_watermark_logo(self):
        return self.watermark_logo is not None and bool(self.watermark_logo)

    @property
    def get_watermark_logo_base64(self):
        return self._image_to_base64(self.watermark_logo)

    @property
    def get_watermark_logo_mime_type(self):
        return self._detect_image_mime_type(self.watermark_logo)

class ExtractorUser(AuditedModel):
    """
    Modelo para usuários extratores de dados.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='extractor_users',
        verbose_name=_('Usuário'),
        help_text=_('Usuário'),
    )
    extraction_agency = models.ForeignKey(
        ExtractionAgency,
        on_delete=models.PROTECT,
        related_name='extractor_users',
        verbose_name=_('Agência de Extração de Dados'),
        help_text=_('Agência de Extração de Dados'),
    )

    class Meta:
        db_table = 'extr_extractor'
        verbose_name = _('Usuário Extrator')
        verbose_name_plural = _('Usuários Extratores')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]
        unique_together = ['user', 'extraction_agency']
    def __str__(self):
        """Retorna uma representação legível do usuário extrator."""
        return f"{self.user.get_full_name()} - {self.extraction_agency.acronym}"

class ExtractionUnitExtractor(AuditedModel):
    """
    Modelo para usuários extratores de dados.
    Representa o extrator que extrai dados de uma unidade de extração.
    Relação NxN entre ExtractionUnit e ExtractorUser.
    """

    extraction_unit = models.ForeignKey(
        ExtractionUnit,
        on_delete=models.PROTECT,
        related_name='extraction_unit_extractors',
        verbose_name=_('Unidade de Extração'),
        help_text=_('Unidade de Extração'),
    )
    extractor = models.ForeignKey(
        ExtractorUser,
        on_delete=models.PROTECT,
        related_name='extraction_unit_extractors',
        verbose_name=_('Extrator'),
        help_text=_('Extrator'),
    )

    class Meta:
        db_table = 'extr_unit_extractor'
        verbose_name = _('Extrator de Unidade de Extração')
        verbose_name_plural = _('Extratores de Unidades de Extração')
        ordering = ['-created_at']
        unique_together = ['extraction_unit', 'extractor']

    def __str__(self):
        """Retorna uma representação legível do extrator de extração de dados."""
        return f"{self.extractor.user.get_full_name()} - {self.extraction_unit.acronym}"

class ExtractionUnitStorageMedia(AuditedModel):
    """
    Modelo para meio de armazenamento.
    Uma extraction unit pode ter vários meios de armazenamento.
    Representa o meio de armazenamento onde material submetido à extração é guardado.
    Ex: "HD 001, Servidor de Arquivos, Guardian, etc.
    """
    extraction_unit = models.ForeignKey(
        ExtractionUnit,
        on_delete=models.PROTECT,
        related_name='storage_medias',
        verbose_name=_('Unidade de Extração'),
        help_text=_('Unidade de Extração'),
    )
    acronym = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Sigla'),
    )
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Nome'),
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Descrição'),
        help_text=_('Descrição do meio de armazenamento'),
    )


    class Meta:
        db_table = 'extr_storage_media'
        verbose_name = _('Meio de Armazenamento')
        verbose_name_plural = _('Meios de Armazenamento')
        ordering = ['-created_at']
        unique_together = ['extraction_unit', 'acronym', 'name']
    def __str__(self):
        """Retorna uma representação legível do meio de armazenamento."""
        return self.name

class ExtractionUnitEvidenceLocation(AuditedModel):
    """
    Modelo para localização de armazenamento de evidências.
    Uma extraction unit pode ter vários locais de armazenamento de evidências.
    Representa o local onde evidência submetida à extração é guardada. 
    Ex: "Sala 001, Armário 001, Prateleira 001, Slot 001, etc.
    """
    TO_DO = 'to_do'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    EVIDENCE_STORAGE_LOCATION_TYPE_CHOICES = [
        (TO_DO, _('Para fazer')),
        (IN_PROGRESS, _('Em progresso')),
        (DONE, _('Finalizado')),
    ]
    extraction_unit = models.ForeignKey(
        ExtractionUnit,
        on_delete=models.PROTECT,
        related_name='evidencestored_locations',
        verbose_name=_('Unidade de Extração'),
        help_text=_('Unidade de Extração'),
    )

    type = models.CharField(
        max_length=20,
        choices=EVIDENCE_STORAGE_LOCATION_TYPE_CHOICES,
        null=False,
        blank=False,
        default=TO_DO,
        verbose_name=_('Tipo'),
        help_text=_('Tipo do local de armazenamento de evidências'),
    )

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Nome'),
        help_text=_('Nome do local de armazenamento de evidências'),
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Descrição'),
        help_text=_('Descrição do local de armazenamento'),
    )
    shelf_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Prateleira'),
        help_text=_('Nome da prateleira do local de armazenamento de evidências'),
    )
    slot_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Nome do Slot'),
        help_text=_('Nome do slot do local de armazenamento de evidências'),
    )

    class Meta:
        db_table = 'extr_evidence_location'
        verbose_name = _('Local de Armazenamento de Evidências')
        verbose_name_plural = _('Locais de Armazenamento de Evidências')
        ordering = ['-created_at']
        unique_together = ['extraction_unit', 'name']