from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
import base64

from apps.core.models import AuditedModel
from apps.base_tables.models import (
    AgencyUnit, EmployeePosition, Agency, Organization
)

class UserProfile(AuditedModel):
    THEME_CHOICES = [
        ('light', _('Claro')),
        ('dark', _('Escuro')),
    ]
    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Usuário')
    )
    
    agency_unit = models.ForeignKey(
        AgencyUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='user_profiles',
        verbose_name=_('Unidade Operacional')
    )
    employee_position = models.ForeignKey(
        EmployeePosition,
        on_delete=models.PROTECT,
        related_name='user_profiles',
        null=True,
        blank=True,
        verbose_name=_('Cargo')
    )
    employee_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Matrícula'
    )
    personal_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='CPF'
    )
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name='Telefone')
    mobile_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name='Celular')
    
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        verbose_name=_('Tema')
    )
    
    profile_image = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_('Foto de Perfil'),
        help_text=_('Imagem de perfil do usuário armazenada no banco de dados')
    )
    

    class Meta:
        db_table = 'user_profile'
        verbose_name = _('Conta do Usuário')
        verbose_name_plural = _('Contas de Usuário')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"

    @property
    def has_profile_image(self):
        """Verifica se o perfil tem uma imagem"""
        return self.profile_image is not None and bool(self.profile_image)

    @property
    def get_profile_image_base64(self):
        """Retorna a imagem de perfil em base64 para exibição"""
        if self.profile_image:
            try:
                return base64.b64encode(self.profile_image).decode('utf-8')
            except Exception:
                return None
        return None


    def clean(self):
        errors = {}

        # Check employee_id uniqueness
        if self.employee_id:
            employee_id_exists = UserProfile.objects.exclude(pk=self.pk).filter(
                employee_id=self.employee_id
            ).exists()
            if employee_id_exists:
                errors['employee_id'] = _('Já existe uma conta com a matrícula informada.')
                
        # Check personal_id uniqueness
        if self.personal_id:
            personal_id_exists = UserProfile.objects.exclude(pk=self.pk).filter(
                personal_id=self.personal_id
            ).exists()
            if personal_id_exists:
                errors['personal_id'] = _('Já existe uma conta com o CPF informado.')

        # Check email uniqueness
        if self.user and self.user.email:
            email_exists = UserProfile.objects.exclude(pk=self.pk).filter(
                user__email=self.user.email
            ).exists()
            if email_exists:
                errors['user'] = _('Já existe uma conta com o email informado.')

        if errors:
            raise ValidationError(errors)

