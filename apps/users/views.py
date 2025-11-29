"""
Views para o app users
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect


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
