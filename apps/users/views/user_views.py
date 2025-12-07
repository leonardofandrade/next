"""
Views para o app users - Refatoradas usando BaseService e BaseViews
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.views.generic import DetailView, UpdateView, View, ListView
from django.urls import reverse
from django.db.models import QuerySet
from django.conf import settings
from typing import Dict, Any

from apps.core.mixins.views import ServiceMixin
from apps.users.models import UserProfile
from apps.users.forms import UserProfileForm, ChangePasswordForm
from apps.users.services import UserProfileService
from apps.core.services.base import ServiceException
from apps.cases.models import Case
from apps.cases.forms import CaseSearchForm
from apps.cases.services import CaseService


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


class UserProfileDetailView(LoginRequiredMixin, ServiceMixin, DetailView):
    """
    View para visualizar o perfil do usuário.
    """
    model = UserProfile
    service_class = UserProfileService
    template_name = 'users/profile_view.html'
    context_object_name = 'profile'
    
    def get_object(self):
        """Get or create user profile"""
        service = self.get_service()
        return service.get_or_create_profile(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Meu Perfil'
        context['page_description'] = 'Visualize e edite suas informações pessoais'
        return context


class UserProfileUpdateView(LoginRequiredMixin, ServiceMixin, UpdateView):
    """
    View para editar o perfil do usuário.
    """
    model = UserProfile
    form_class = UserProfileForm
    service_class = UserProfileService
    template_name = 'users/profile_edit.html'
    context_object_name = 'profile'
    
    def get_object(self):
        """Get or create user profile"""
        service = self.get_service()
        return service.get_or_create_profile(self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle form submission"""
        service = self.get_service()
        profile = self.get_object()
        
        # Extract profile data and user data
        profile_data = {}
        user_data = {}
        
        for field in form.Meta.fields:
            if field in form.cleaned_data:
                profile_data[field] = form.cleaned_data[field]
        
        # Extract user fields
        if 'first_name' in form.cleaned_data:
            user_data['first_name'] = form.cleaned_data['first_name']
        if 'last_name' in form.cleaned_data:
            user_data['last_name'] = form.cleaned_data['last_name']
        if 'email' in form.cleaned_data:
            user_data['email'] = form.cleaned_data['email']
        
        try:
            # Update profile
            profile = service.update_profile(profile, profile_data, user_data)
            
            # Handle profile image
            if form.cleaned_data.get('remove_image'):
                service.update_profile_image(profile, None, remove=True)
            elif form.cleaned_data.get('profile_image_file'):
                image_file = form.cleaned_data['profile_image_file']
                service.update_profile_image(profile, image_file.read())
            
            messages.success(self.request, _('Perfil atualizado com sucesso!'))
            return redirect('users:profile_view')
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Editar Perfil'
        context['page_description'] = 'Atualize suas informações pessoais'
        return context


class ChangePasswordView(LoginRequiredMixin, ServiceMixin, View):
    """
    View para alterar a senha do usuário.
    """
    service_class = UserProfileService
    template_name = 'users/change_password.html'
    
    def get(self, request):
        form = ChangePasswordForm(request.user)
        context = {
            'form': form,
            'page_title': 'Alterar Senha',
            'page_description': 'Atualize sua senha de acesso',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = ChangePasswordForm(request.user, request.POST)
        
        if form.is_valid():
            service = self.get_service()
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']
            
            try:
                service.change_password(request.user, current_password, new_password)
                # Mantém o usuário logado após mudar a senha
                update_session_auth_hash(request, request.user)
                messages.success(request, _('Senha alterada com sucesso!'))
                return redirect('users:profile_view')
            except ServiceException as e:
                self.handle_service_exception(e)
        
        context = {
            'form': form,
            'page_title': 'Alterar Senha',
            'page_description': 'Atualize sua senha de acesso',
        }
        return render(request, self.template_name, context)


@login_required
def profile_image(request, pk):
    """
    View para servir a imagem de perfil do usuário.
    """
    profile = get_object_or_404(UserProfile, pk=pk)
    
    # Verifica se o usuário tem permissão para ver a imagem
    if profile.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse(status=403)
    
    if profile.profile_image:
        return HttpResponse(profile.profile_image, content_type='image/jpeg')
    else:
        # Retorna uma imagem padrão ou 404
        return HttpResponse(status=404)


# Mantidas para compatibilidade com URLs
def profile_view(request):
    """Wrapper para UserProfileDetailView"""
    view = UserProfileDetailView.as_view()
    return view(request)


def profile_edit(request):
    """Wrapper para UserProfileUpdateView"""
    view = UserProfileUpdateView.as_view()
    return view(request)


def change_password(request):
    """Wrapper para ChangePasswordView"""
    view = ChangePasswordView.as_view()
    return view(request)

