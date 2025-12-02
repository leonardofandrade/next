"""
Views para o app extractions
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView
from django.db.models import Q
from apps.cases.models import Case, Extraction
from apps.extractions.forms import ExtractionSearchForm


class ExtractionListView(LoginRequiredMixin, ListView):
    """
    Lista todas as extrações com filtros de busca
    """
    model = Extraction
    template_name = 'extractions/extraction_list.html'
    context_object_name = 'page_obj'
    paginate_by = 25
    
    def get_queryset(self):
        """
        Retorna o queryset filtrado com base nos parâmetros de busca
        """
        queryset = Extraction.objects.filter(
            deleted_at__isnull=True,
            case_device__deleted_at__isnull=True,
            case_device__case__deleted_at__isnull=True
        ).select_related(
            'case_device__device_category',
            'case_device__device_model__brand',
            'case_device__case',
            'assigned_to__user',
            'assigned_by',
            'started_by__user',
            'finished_by__user',
            'storage_media'
        ).order_by('-created_at')
        
        form = ExtractionSearchForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                # Busca por modelo, IMEI ou proprietário
                queryset = queryset.filter(
                    Q(case_device__device_model__name__icontains=search) |
                    Q(case_device__device_model__brand__name__icontains=search) |
                    Q(case_device__imei_01__icontains=search) |
                    Q(case_device__imei_02__icontains=search) |
                    Q(case_device__imei_03__icontains=search) |
                    Q(case_device__imei_04__icontains=search) |
                    Q(case_device__imei_05__icontains=search) |
                    Q(case_device__owner_name__icontains=search)
                )
            
            case_number = form.cleaned_data.get('case_number')
            if case_number:
                queryset = queryset.filter(
                    case_device__case__number__icontains=case_number
                )
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            extraction_unit = form.cleaned_data.get('extraction_unit')
            if extraction_unit:
                queryset = queryset.filter(
                    case_device__case__extraction_unit=extraction_unit
                )
            
            assigned_to = form.cleaned_data.get('assigned_to')
            if assigned_to:
                # assigned_to é um User, mas precisamos filtrar por ExtractorUser
                queryset = queryset.filter(assigned_to__user=assigned_to)
            
            extraction_result = form.cleaned_data.get('extraction_result')
            if extraction_result:
                queryset = queryset.filter(extraction_result=extraction_result)
            
            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            
            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Adiciona o formulário de busca e total_count ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Extrações'
        context['page_icon'] = 'fa-database'
        context['form'] = ExtractionSearchForm(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context


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
