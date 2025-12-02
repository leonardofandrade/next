"""
Views para o app extractions
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from apps.cases.models import Case, Extraction


class CaseExtractionsView(LoginRequiredMixin, DetailView):
    """
    Exibe as extrações de um processo de extração
    """
    model = Case
    template_name = 'extractions/case_extractions.html'
    context_object_name = 'case'
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados
        """
        return Case.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona as extrações do caso ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        
        # Busca extrações através dos dispositivos do caso
        # Filtra apenas dispositivos não deletados e suas extrações
        extractions = Extraction.objects.filter(
            case_device__case=case,
            case_device__deleted_at__isnull=True,
            deleted_at__isnull=True
        ).select_related(
            'case_device__device_category',
            'case_device__device_model__brand',
            'assigned_to',
            'assigned_by',
            'started_by',
            'finished_by',
            'storage_media'
        ).order_by('-created_at')
        
        context['page_title'] = f'Extrações - Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-database'
        context['extractions'] = extractions
        return context
