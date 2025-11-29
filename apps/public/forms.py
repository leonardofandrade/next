"""
Forms para o app public
"""
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    """
    Formulário de login que suporta autenticação por:
    - Email
    - Username
    - Employee ID (através do CustomAuthBackend)
    """
    username = forms.CharField(
        label='Usuário',
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-mail, usuário ou matrícula',
            'autofocus': True,
            'autocomplete': 'username'
        }),
        help_text='Digite seu e-mail, nome de usuário ou matrícula'
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label='Lembrar-me',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Tenta autenticar usando o CustomAuthBackend
            # O backend suporta: email, username ou employee_id
            user = authenticate(
                request=None,  # Pode ser None para forms
                username=username,
                password=password
            )
            
            if user is None:
                # Tenta verificar se o usuário existe mas a senha está errada
                from django.contrib.auth import get_user_model
                from apps.users.models import UserProfile
                
                User = get_user_model()
                user_found = None
                
                # Tenta encontrar por username
                try:
                    user_found = User.objects.get(username=username)
                except User.DoesNotExist:
                    pass
                
                # Tenta encontrar por email
                if not user_found and '@' in username:
                    try:
                        user_found = User.objects.get(email=username)
                    except User.DoesNotExist:
                        pass
                
                # Tenta encontrar por employee_id
                if not user_found:
                    try:
                        profile = UserProfile.objects.get(employee_id=username)
                        user_found = profile.user
                    except UserProfile.DoesNotExist:
                        pass
                
                if user_found:
                    if not user_found.is_active:
                        raise ValidationError(
                            'Esta conta está desativada. Entre em contato com o administrador.'
                        )
                    raise ValidationError(
                        'Senha incorreta. Verifique sua senha e tente novamente.'
                    )
                else:
                    raise ValidationError(
                        'Credenciais inválidas. Verifique seu usuário e senha.'
                    )
            
            if not user.is_active:
                raise ValidationError(
                    'Esta conta está desativada. Entre em contato com o administrador.'
                )
            
            cleaned_data['user'] = user
        
        return cleaned_data

