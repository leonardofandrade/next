"""
Views para o app users
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse

from apps.users.models import UserProfile
from apps.users.forms import UserProfileForm, ChangePasswordForm


@login_required
def home_view(request):
    """
    View da página inicial do usuário autenticado.
    """
    context = {
        'page_title': 'Página Inicial',
        'page_description': 'Bem-vindo ao sistema de gestão de extrações digitais',
        'page_icon': 'fa-home',
    }
    return render(request, 'users/home.html', context)


@login_required
def logout_view(request):
    """
    View para logout de usuários.
    """
    logout(request)
    return redirect('public:login')


@login_required
def profile_view(request):
    """
    View para visualizar o perfil do usuário.
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile,
        'page_title': 'Meu Perfil',
        'page_description': 'Visualize e edite suas informações pessoais',
    }
    return render(request, 'users/profile_view.html', context)


@login_required
def profile_edit(request):
    """
    View para editar o perfil do usuário.
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Perfil atualizado com sucesso!'))
            return redirect('users:profile_view')
    else:
        form = UserProfileForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
        'profile': profile,
        'page_title': 'Editar Perfil',
        'page_description': 'Atualize suas informações pessoais',
    }
    return render(request, 'users/profile_edit.html', context)


@login_required
def change_password(request):
    """
    View para alterar a senha do usuário.
    """
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # Mantém o usuário logado após mudar a senha
            update_session_auth_hash(request, request.user)
            messages.success(request, _('Senha alterada com sucesso!'))
            return redirect('users:profile_view')
    else:
        form = ChangePasswordForm(request.user)
    
    context = {
        'form': form,
        'page_title': 'Alterar Senha',
        'page_description': 'Atualize sua senha de acesso',
    }
    return render(request, 'users/change_password.html', context)


@login_required
def profile_image(request, pk):
    """
    View para servir a imagem de perfil do usuário.
    """
    profile = get_object_or_404(UserProfile, pk=pk)
    
    if profile.profile_image:
        return HttpResponse(profile.profile_image, content_type='image/jpeg')
    else:
        # Retorna uma imagem padrão ou 404
        return HttpResponse(status=404)
