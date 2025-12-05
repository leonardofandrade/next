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


class MyExtractionsView(LoginRequiredMixin, ServiceMixin, ListView):
    """
    Lista as extrações atribuídas ao usuário extrator logado
    """
    model = Extraction
    service_class = ExtractionService
    search_form_class = ExtractionSearchForm
    template_name = 'extractions/my_extractions.html'
    context_object_name = 'page_obj'
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
        context['page_title'] = 'Minhas Extrações'
        context['page_icon'] = 'fa-user-check'
        context['form'] = self.search_form_class(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context

