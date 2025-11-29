"""
Views para o app public
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

from apps.public.forms import LoginForm


class LandingView(TemplateView):
    """
    View para a página inicial (landing page) do sistema.
    Exibe informações sobre o sistema e opções de login.
    """
    template_name = 'public/landing.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Se o usuário já está autenticado, redireciona para a home
        if request.user.is_authenticated:
            return redirect('users:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Bem-vindo ao Sistema de Extrações Digitais'
        return context


@method_decorator([csrf_protect, never_cache], name='dispatch')
class LoginView(FormView):
    """
    View para login de usuários.
    Suporta autenticação por email, username ou employee_id.
    """
    template_name = 'public/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('users:home')
    
    def dispatch(self, request, *args, **kwargs):
        # Se o usuário já está autenticado, redireciona para a home
        if request.user.is_authenticated:
            return redirect('users:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Login - Sistema de Extrações'
        return context
    
    def form_valid(self, form):
        """
        Processa o login quando o formulário é válido.
        """
        user = form.cleaned_data['user']
        remember_me = form.cleaned_data.get('remember_me', False)
        
        # Faz o login
        login(self.request, user)
        
        # Configura a sessão baseado no "lembrar-me"
        if remember_me:
            # Mantém a sessão por 30 dias
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            # Expira quando o navegador fechar
            self.request.session.set_expiry(0)
        
        # Mensagem de sucesso
        messages.success(
            self.request,
            f'Bem-vindo, {user.get_full_name() or user.username}!'
        )
        
        # Verifica se há um next na URL para redirecionar
        next_url = self.request.GET.get('next')
        if next_url:
            return redirect(next_url)
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Processa o login quando o formulário é inválido.
        """
        # Adiciona mensagem de erro
        messages.error(
            self.request,
            'Não foi possível fazer login. Verifique suas credenciais e tente novamente.'
        )
        return super().form_invalid(form)


@login_required
def logout_view(request):
    """
    View para logout de usuários.
    """
    username = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'Até logo, {username}! Você foi desconectado com sucesso.')
    return redirect('public:landing')
