from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.users.models import UserProfile
from apps.base_tables.models import AgencyUnit, EmployeePosition
import base64


class UserProfileForm(forms.ModelForm):
    """Form para edição de perfil do usuário"""
    
    # Campos do User
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label=_('Nome'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label=_('Sobrenome'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'})
    )
    email = forms.EmailField(
        required=True,
        label=_('E-mail'),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'})
    )
    
    # Campo para upload de imagem
    profile_image_file = forms.ImageField(
        required=False,
        label=_('Foto de Perfil'),
        help_text=_('Formatos aceitos: JPG, PNG. Tamanho máximo: 2MB'),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    
    remove_image = forms.BooleanField(
        required=False,
        label=_('Remover foto atual'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'agency_unit', 'employee_position', 'employee_id', 'personal_id',
            'phone_number', 'mobile_number', 'theme'
        ]
        widgets = {
            'agency_unit': forms.Select(attrs={'class': 'form-select'}),
            'employee_position': forms.Select(attrs={'class': 'form-select'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matrícula'}),
            'personal_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(85) 3333-3333'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(85) 99999-9999'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Preenche campos do User se houver instância
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        # Filtra apenas registros não deletados
        self.fields['agency_unit'].queryset = AgencyUnit.objects.filter(deleted_at__isnull=True)
        self.fields['employee_position'].queryset = EmployeePosition.objects.filter(deleted_at__isnull=True)
    
    def clean_profile_image_file(self):
        """Valida o tamanho da imagem"""
        image = self.cleaned_data.get('profile_image_file')
        if image:
            # Limita a 2MB
            if image.size > 2 * 1024 * 1024:
                raise ValidationError(_('A imagem deve ter no máximo 2MB.'))
        return image
    
    def clean_email(self):
        """Valida unicidade do email"""
        email = self.cleaned_data.get('email')
        if email:
            # Verifica se já existe outro usuário com esse email
            user_exists = User.objects.filter(email=email).exclude(
                pk=self.instance.user.pk if self.instance and self.instance.user else None
            ).exists()
            if user_exists:
                raise ValidationError(_('Já existe um usuário com este e-mail.'))
        return email
    
    def save(self, commit=True):
        """Salva o perfil e atualiza o User"""
        profile = super().save(commit=False)
        
        # Atualiza dados do User
        if profile.user:
            profile.user.first_name = self.cleaned_data.get('first_name')
            profile.user.last_name = self.cleaned_data.get('last_name')
            profile.user.email = self.cleaned_data.get('email')
            if commit:
                profile.user.save()
        
        # Processa a imagem de perfil
        if self.cleaned_data.get('remove_image'):
            profile.profile_image = None
        elif self.cleaned_data.get('profile_image_file'):
            image_file = self.cleaned_data.get('profile_image_file')
            profile.profile_image = image_file.read()
        
        if commit:
            profile.save()
        
        return profile


class ChangePasswordForm(forms.Form):
    """Form para alteração de senha"""
    
    current_password = forms.CharField(
        label=_('Senha Atual'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua senha atual'})
    )
    new_password = forms.CharField(
        label=_('Nova Senha'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite a nova senha'})
    )
    confirm_password = forms.CharField(
        label=_('Confirmar Nova Senha'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme a nova senha'})
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        """Valida a senha atual"""
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError(_('Senha atual incorreta.'))
        return current_password
    
    def clean(self):
        """Valida se as senhas coincidem"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError(_('As senhas não coincidem.'))
        
        return cleaned_data
    
    def save(self):
        """Atualiza a senha do usuário"""
        new_password = self.cleaned_data.get('new_password')
        self.user.set_password(new_password)
        self.user.save()
        return self.user
