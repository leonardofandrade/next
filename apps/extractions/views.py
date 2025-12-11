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
from django.http import JsonResponse
from django.template.loader import render_to_string

from apps.core.mixins.views import ServiceMixin, ExtractionUnitFilterMixin
from apps.cases.models import Case, Extraction
from apps.extractions.forms import ExtractionSearchForm, ExtractionFinishForm, BruteForceFinishForm
from apps.extractions.services import ExtractionService
from apps.core.services.base import ServiceException, ValidationServiceException


class ExtractionListView(ExtractionUnitFilterMixin, LoginRequiredMixin, ServiceMixin, ListView):
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
    template_name = 'cases/case_extractions.html'
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
        
        # Add extractions count
        context['extractions_count'] = Extraction.objects.filter(
            case_device__case=case,
            deleted_at__isnull=True
        ).count()
        
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
        
        # Verifica se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            extraction = service.unassign_from_me(pk)
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Atribuição removida com sucesso!'
                })
            messages.success(request, 'Atribuição removida com sucesso!')
        except ServiceException as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        if not is_ajax:
            return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer or 'users/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionStartView(LoginRequiredMixin, View):
    """Inicia uma extração, atribuindo ao usuário se necessário"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        notes = request.POST.get('notes', '')
        
        # Verifica se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            extraction = service.start(pk, notes=notes if notes else None)
            if is_ajax:
                message = 'Extração iniciada com sucesso!'
                if not extraction.assigned_to or extraction.assigned_to.user == request.user:
                    if not extraction.assigned_to:
                        message = 'Extração atribuída automaticamente a você e iniciada com sucesso!'
                return JsonResponse({
                    'success': True,
                    'message': message
                })
            else:
                if not extraction.assigned_to or extraction.assigned_to.user == request.user:
                    if not extraction.assigned_to:
                        messages.info(request, 'Extração atribuída automaticamente a você.')
                messages.success(request, 'Extração iniciada com sucesso!')
        except ServiceException as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            else:
                if isinstance(e, ValidationServiceException):
                    messages.warning(request, str(e))
                else:
                    messages.error(request, str(e))
                extraction = service.get_object(pk)
        
        if not is_ajax:
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
        notes = request.POST.get('notes', '')
        
        # Verifica se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            extraction = service.pause(pk, notes=notes if notes else None)
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Extração pausada com sucesso!'
                })
            messages.success(request, 'Extração pausada com sucesso!')
        except ServiceException as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        if not is_ajax:
            return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer or 'users/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionResumeView(LoginRequiredMixin, View):
    """Retoma uma extração pausada"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        # Verifica se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            extraction = service.resume(pk)
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Extração retomada com sucesso!'
                })
            messages.success(request, 'Extração retomada com sucesso!')
        except ServiceException as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        if not is_ajax:
            return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer or 'users/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionCancelView(LoginRequiredMixin, View):
    """Cancela uma extração em andamento, revertendo para status pending"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        # Verifica se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            extraction = service.cancel(pk)
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Extração cancelada com sucesso! A extração voltou para o status "Aguardando Extrator".'
                })
            messages.success(request, 'Extração cancelada com sucesso! A extração voltou para o status "Aguardando Extrator".')
        except ServiceException as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        if not is_ajax:
            return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer or 'users/my-extractions' in referer:
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


class ExtractionFinishFormModalView(LoginRequiredMixin, View):
    """Retorna o formulário de finalização de extração para modal AJAX"""
    
    def get(self, request, pk):
        service = ExtractionService(user=request.user)
        
        try:
            extraction = service.get_object(pk)
            
            if not service.can_be_finished(extraction.pk):
                return JsonResponse({
                    'success': False,
                    'error': 'Apenas extrações em andamento ou pausadas podem ser finalizadas. Apenas o responsável pela extração pode finalizá-la.'
                }, status=403)
            
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
            
            form = ExtractionFinishForm(
                initial=initial_data,
                extraction_unit=extraction.case_device.case.extraction_unit
            )
            
            # Renderiza apenas o formulário
            form_html = render_to_string('extractions/includes/finish_form_modal.html', {
                'form': form,
                'extraction': extraction
            }, request=request)
            
            return JsonResponse({
                'success': True,
                'html': form_html
            })
        except ServiceException as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


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
            # Se for AJAX, retorna erro em JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Por favor, corrija os erros no formulário.',
                    'errors': form.errors
                }, status=400)
            
            messages.error(request, 'Por favor, corrija os erros no formulário.')
            return render(request, 'extractions/extraction_finish_form.html', {
                'extraction': extraction,
                'form': form,
                'page_title': f'Finalizar Extração #{extraction.pk}',
                'page_icon': 'fa-check-circle'
            })
        
        try:
            service.finish(pk, form.cleaned_data)
            
            # Se for AJAX, retorna JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Extração finalizada com sucesso!'
                })
            
            messages.success(request, 'Extração finalizada com sucesso!')
        except ServiceException as e:
            # Se for AJAX, retorna erro em JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, str(e))
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer or 'users/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class BruteForceStartView(LoginRequiredMixin, View):
    """Inicia a força bruta para uma extração"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        notes = request.POST.get('notes', '')
        
        # Verifica se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            extraction = service.start_brute_force(pk, notes=notes if notes else None)
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Força bruta iniciada com sucesso!'
                })
            messages.success(request, 'Força bruta iniciada com sucesso!')
        except ServiceException as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            if isinstance(e, ValidationServiceException):
                messages.warning(request, str(e))
            else:
                messages.error(request, str(e))
            extraction = service.get_object(pk)
        
        if not is_ajax:
            return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer or 'users/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class BruteForceFinishFormModalView(LoginRequiredMixin, View):
    """Retorna o formulário de finalização de força bruta para modal AJAX"""
    
    def get(self, request, pk):
        service = ExtractionService(user=request.user)
        
        try:
            extraction = service.get_object(pk)
            
            if not service.can_finish_brute_force(extraction.pk):
                return JsonResponse({
                    'success': False,
                    'error': 'Não é possível finalizar a força bruta. Verifique se ela foi iniciada e se você é o responsável pela extração.'
                }, status=403)
            
            # Cria o formulário com dados iniciais da extração
            initial_data = {
                'brute_force_result': extraction.brute_force_result,
                'brute_force_results_notes': extraction.brute_force_results_notes,
            }
            
            form = BruteForceFinishForm(initial=initial_data)
            
            # Renderiza apenas o formulário
            form_html = render_to_string('extractions/includes/brute_force_finish_modal.html', {
                'form': form,
                'extraction': extraction
            }, request=request)
            
            return JsonResponse({
                'success': True,
                'html': form_html
            })
        except ServiceException as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class BruteForceFinishView(LoginRequiredMixin, View):
    """Finaliza a força bruta para uma extração"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        extraction = service.get_object(pk)
        
        # Valida o formulário
        form = BruteForceFinishForm(request.POST)
        
        if not form.is_valid():
            # Se for AJAX, retorna erro em JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Por favor, corrija os erros no formulário.',
                    'errors': form.errors
                }, status=400)
            
            messages.error(request, 'Por favor, corrija os erros no formulário.')
            return render(request, 'extractions/brute_force_finish_form.html', {
                'extraction': extraction,
                'form': form,
                'page_title': f'Finalizar Força Bruta - Extração #{extraction.pk}',
                'page_icon': 'fa-unlock-alt'
            })
        
        try:
            service.finish_brute_force(pk, form.cleaned_data)
            
            # Se for AJAX, retorna JSON
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Força bruta finalizada com sucesso!'
                })
            
            messages.success(request, 'Força bruta finalizada com sucesso!')
        except ServiceException as e:
            # Se for AJAX, retorna erro em JSON
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, str(e))
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """Redireciona de acordo com o referer ou para as extrações do caso"""
        referer = request.META.get('HTTP_REFERER')
        if referer:
            if 'extractions/my-extractions' in referer or 'users/my-extractions' in referer:
                return redirect('users:my_extractions')
            if 'extractions/list' in referer:
                return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)
