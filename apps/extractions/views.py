"""
Views para o app extractions - Refatoradas usando BaseService e BaseViews
"""
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, View, ListView
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.db.models import QuerySet
from typing import Dict, Any

from apps.core.mixins.views import ServiceMixin
from apps.cases.models import Case, Extraction
from apps.extractions.forms import ExtractionSearchForm, ExtractionFinishForm
from apps.extractions.services import ExtractionService
from apps.core.services.base import ServiceException


class ExtractionListView(LoginRequiredMixin, ServiceMixin, ListView):
    """
    Lista todas as extrações com filtros de busca
    """
    model = Extraction
    service_class = ExtractionService
    search_form_class = ExtractionSearchForm
    template_name = 'extractions/extraction_list.html'
    context_object_name = 'extractions'
    paginate_by = settings.PAGINATE_BY
    
    def get_queryset(self) -> QuerySet:
        """Get filtered queryset using service"""
        service = self.get_service()
        filters = self.get_filters()
        
        try:
            return service.list_filtered(filters)
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.model.objects.none()
    
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
        context['page_title'] = 'Extrações'
        context['page_icon'] = 'fa-database'
        context['form'] = self.search_form_class(self.request.GET or None)
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
        """Filtra apenas casos não deletados"""
        return Case.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        service = ExtractionService(user=self.request.user)
        
        # Busca extrações através dos dispositivos do caso
        extractions = service.get_extractions_by_case(case.pk)
        
        # Verifica se há dispositivos sem extração
        devices_without_extraction = case.case_devices.filter(
            deleted_at__isnull=True
        ).exclude(
            pk__in=Extraction.objects.values_list('case_device_id', flat=True)
        ).exists()
        
        context['page_title'] = f'Extrações - Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-database'
        context['extractions'] = extractions
        context['has_devices_without_extractions'] = devices_without_extraction
        return context


class ExtractionAssignToMeView(LoginRequiredMixin, View):
    """Atribui a extração ao usuário extrator logado"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        try:
            extraction = service.assign_to_me(pk)
            messages.success(request, 'Extração atribuída a você com sucesso!')
        except ServiceException as e:
            if isinstance(e, ValidationServiceException):
                messages.warning(request, str(e))
            else:
                messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionUnassignFromMeView(LoginRequiredMixin, View):
    """Remove a atribuição da extração do usuário extrator logado"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        try:
            extraction = service.unassign_from_me(pk)
            messages.success(request, 'Atribuição removida com sucesso!')
        except ServiceException as e:
            messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionStartView(LoginRequiredMixin, View):
    """Inicia uma extração, atribuindo ao usuário se necessário"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        notes = request.POST.get('notes', '')
        
        try:
            extraction = service.start(pk, notes=notes if notes else None)
            if not extraction.assigned_to or extraction.assigned_to.user == request.user:
                if not extraction.assigned_to:
                    messages.info(request, 'Extração atribuída automaticamente a você.')
            messages.success(request, 'Extração iniciada com sucesso!')
        except ServiceException as e:
            if isinstance(e, ValidationServiceException):
                messages.warning(request, str(e))
            else:
                messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionPauseView(LoginRequiredMixin, View):
    """Pausa uma extração em andamento"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        try:
            extraction = service.pause(pk)
            messages.success(request, 'Extração pausada com sucesso!')
        except ServiceException as e:
            messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionResumeView(LoginRequiredMixin, View):
    """Retoma uma extração pausada"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        try:
            extraction = service.resume(pk)
            messages.success(request, 'Extração retomada com sucesso!')
        except ServiceException as e:
            messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionFinishFormView(LoginRequiredMixin, DetailView):
    """Exibe o formulário de finalização da extração"""
    model = Extraction
    template_name = 'extractions/extraction_finish_form.html'
    context_object_name = 'extraction'
    
    def get_queryset(self):
        """Filtra apenas extrações não deletadas"""
        return Extraction.objects.filter(deleted_at__isnull=True)
    
    def get(self, request, *args, **kwargs):
        """Exibe o formulário de finalização"""
        extraction = self.get_object()
        service = ExtractionService(user=request.user)
        
        try:
            if not service.can_be_finished(extraction.pk):
                messages.error(
                    request,
                    'Apenas extrações em andamento ou pausadas podem ser finalizadas. '
                    'Apenas o responsável pela extração pode finalizá-la.'
                )
                return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)
        except ServiceException as e:
            messages.error(request, str(e))
            return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        extraction = self.get_object()
        
        # Cria o formulário com dados iniciais da extração
        initial_data = {
            'extraction_result': extraction.extraction_result,
            'finished_notes': extraction.finished_notes,
            'extraction_results_notes': extraction.extraction_results_notes,
            'logical_extraction': extraction.logical_extraction,
            'logical_extraction_notes': extraction.logical_extraction_notes,
            'physical_extraction': extraction.physical_extraction,
            'physical_extraction_notes': extraction.physical_extraction_notes,
            'full_file_system_extraction': extraction.full_file_system_extraction,
            'full_file_system_extraction_notes': extraction.full_file_system_extraction_notes,
            'cloud_extraction': extraction.cloud_extraction,
            'cloud_extraction_notes': extraction.cloud_extraction_notes,
            'cellebrite_premium': extraction.cellebrite_premium,
            'cellebrite_premium_notes': extraction.cellebrite_premium_notes,
            'cellebrite_premium_support': extraction.cellebrite_premium_support,
            'cellebrite_premium_support_notes': extraction.cellebrite_premium_support_notes,
            'extraction_size': extraction.extraction_size,
            'storage_media': extraction.storage_media,
        }
        
        context['form'] = ExtractionFinishForm(
            initial=initial_data,
            extraction_unit=extraction.case_device.case.extraction_unit
        )
        context['page_title'] = f'Finalizar Extração #{extraction.pk}'
        context['page_icon'] = 'fa-check-circle'
        
        return context


class ExtractionFinishView(LoginRequiredMixin, View):
    """Finaliza uma extração"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        extraction = service.get_object(pk)
        
        # Valida o formulário
        form = ExtractionFinishForm(
            request.POST,
            extraction_unit=extraction.case_device.case.extraction_unit
        )
        
        if not form.is_valid():
            messages.error(request, 'Por favor, corrija os erros no formulário.')
            return render(request, 'extractions/extraction_finish_form.html', {
                'extraction': extraction,
                'form': form,
                'page_title': f'Finalizar Extração #{extraction.pk}',
                'page_icon': 'fa-check-circle'
            })
        
        try:
            service.finish(pk, form.cleaned_data)
            messages.success(request, 'Extração finalizada com sucesso!')
        except ServiceException as e:
            messages.error(request, str(e))
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)
