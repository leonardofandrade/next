"""
Views relacionadas a extratores
"""
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.contrib import messages
from django.conf import settings
from django.db.models import QuerySet
from typing import Dict, Any

from apps.core.mixins.views import ServiceMixin
from apps.cases.models import Extraction
from apps.extractions.forms import ExtractionSearchForm
from apps.extractions.services import ExtractionService
from apps.core.models import ExtractorUser
from apps.cases.models import Case
from apps.cases.forms import CaseSearchForm
from apps.cases.services import CaseService


class MyExtractionsView(LoginRequiredMixin, ServiceMixin, ListView):
    """
    Lista as extrações atribuídas ao usuário extrator logado
    """
    model = Extraction
    service_class = ExtractionService
    search_form_class = ExtractionSearchForm
    template_name = 'users/extractors/my_extractions.html'
    context_object_name = 'extractions'
    paginate_by = settings.PAGINATE_BY
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica se o usuário é um extrator antes de permitir acesso"""
        try:
            ExtractorUser.objects.get(
                user=request.user,
                deleted_at__isnull=True
            )
        except ExtractorUser.DoesNotExist:
            messages.error(
                request,
                'Você não é um usuário extrator. Apenas extratores podem acessar esta página.'
            )
            return redirect('extractions:list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self) -> QuerySet:
        """Retorna apenas as extrações atribuídas ao usuário extrator logado"""
        service = self.get_service()
        queryset = service.get_my_extractions()
        
        # Aplica filtros do formulário
        filters = self.get_filters()
        if filters:
            queryset = service.apply_filters(queryset, filters)
        
        return queryset
    
    def get_filters(self) -> Dict[str, Any]:
        """Get filters from request"""
        filters = {}
        
        if self.search_form_class:
            form = self.search_form_class(self.request.GET or None)
            if form.is_valid():
                filters = form.cleaned_data
                
        return {k: v for k, v in filters.items() if v}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtém o queryset completo antes da paginação para estatísticas
        queryset = self.get_queryset()
        
        # Estatísticas por status
        context['stats'] = {
            'pending': queryset.filter(status='pending').count(),
            'assigned': queryset.filter(status='assigned').count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'paused': queryset.filter(status='paused').count(),
            'completed': queryset.filter(status='completed').count(),
        }
        
        # Extrações agrupadas por status para exibição em seções (máximo 10 por status)
        context['extractions_by_status'] = {
            'pending': list(queryset.filter(status='pending')[:10]),
            'assigned': list(queryset.filter(status='assigned')[:10]),
            'in_progress': list(queryset.filter(status='in_progress')[:10]),
            'paused': list(queryset.filter(status='paused')[:10]),
        }
        
        context['page_title'] = 'Minhas Extrações'
        context['page_icon'] = 'fa-user-check'
        context['form'] = self.search_form_class(self.request.GET or None)
        context['total_count'] = queryset.count()
        return context


class MyCasesView(LoginRequiredMixin, ServiceMixin, ListView):
    """
    Lista os processos atribuídos ao usuário logado
    """
    model = Case
    service_class = CaseService
    search_form_class = CaseSearchForm
    template_name = 'users/extractors/my_cases.html'
    context_object_name = 'cases'
    paginate_by = settings.PAGINATE_BY
    
    def get_queryset(self) -> QuerySet:
        """Retorna apenas os casos atribuídos ao usuário logado"""
        service = self.get_service()
        queryset = service.get_my_cases()
        
        # Aplica filtros do formulário (removendo assigned_to para garantir segurança)
        filters = self.get_filters()
        # Remove o filtro assigned_to para garantir que sempre filtre apenas pelo usuário logado
        filters.pop('assigned_to', None)
        if filters:
            queryset = service.apply_filters(queryset, filters)
        
        return queryset
    
    def get_filters(self) -> Dict[str, Any]:
        """Get filters from request"""
        filters = {}
        
        if self.search_form_class:
            form = self.search_form_class(self.request.GET or None)
            if form.is_valid():
                filters = form.cleaned_data
                
        return {k: v for k, v in filters.items() if v}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Meus Processos'
        context['page_icon'] = 'fa-folder-open'
        # Remove o campo assigned_to do formulário para evitar confusão
        form = self.search_form_class(self.request.GET or None)
        if 'assigned_to' in form.fields:
            del form.fields['assigned_to']
        context['form'] = form
        context['total_count'] = self.get_queryset().count()
        return context

