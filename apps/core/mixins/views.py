"""
Base mixins and views for common patterns
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from typing import Optional, Dict, Any
from django.core.paginator import Paginator
from django.db.models import QuerySet

from apps.core.services.base import BaseService, ServiceException


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin that requires user to be staff or superuser"""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class StaffOrExtractorRequiredMixin(UserPassesTestMixin):
    """Mixin that requires user to be staff, superuser, or an extractor"""
    
    def test_func(self):
        user = self.request.user
        
        # Staff e superuser sempre têm acesso
        if user.is_staff or user.is_superuser:
            return True
        
        # Verifica se é um extrator ativo
        try:
            from apps.core.models import ExtractorUser
            return ExtractorUser.objects.filter(
                user=user,
                deleted_at__isnull=True
            ).exists()
        except Exception:
            return False


class AjaxResponseMixin:
    """Mixin to handle AJAX requests"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return self.ajax_dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)
    
    def ajax_dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class ServiceMixin:
    """Mixin to integrate services with views"""
    
    service_class = None
    
    def get_service(self) -> BaseService:
        """Get service instance with current user"""
        if self.service_class is None:
            raise NotImplementedError("service_class must be defined")
        return self.service_class(user=self.request.user)
    
    def handle_service_exception(self, exception: ServiceException):
        """Handle service exceptions"""
        messages.error(self.request, str(exception))


class BaseListView(LoginRequiredMixin, StaffOrExtractorRequiredMixin, ServiceMixin, ListView):
    """Base list view with search and pagination"""
    
    paginate_by = 25
    search_form_class = None

    def _build_search_form(self):
        """Build search form passing user when supported."""
        if not self.search_form_class:
            return None

        try:
            return self.search_form_class(self.request.GET or None, user=self.request.user)
        except TypeError:
            # Backwards compatibility for forms that don't accept `user`
            return self.search_form_class(self.request.GET or None)
    
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
            form = self._build_search_form()
            if form.is_valid():
                filters = form.cleaned_data
                
        return {k: v for k, v in filters.items() if v}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.search_form_class:
            context['search_form'] = self._build_search_form()
            
        return context


class BaseDetailView(LoginRequiredMixin, StaffOrExtractorRequiredMixin, ServiceMixin, DetailView):
    """Base detail view"""
    
    def get_object(self):
        """Get object using service"""
        service = self.get_service()
        
        try:
            return service.get_object(self.kwargs['pk'])
        except ServiceException as e:
            self.handle_service_exception(e)
            return None


class BaseCreateView(LoginRequiredMixin, StaffOrExtractorRequiredMixin, ServiceMixin, CreateView):
    """Base create view using service"""
    
    def form_valid(self, form):
        """Handle form validation using service"""
        service = self.get_service()
        
        try:
            self.object = service.create(form.cleaned_data)
            messages.success(
                self.request, 
                _(f'{self.model._meta.verbose_name} criado com sucesso!')
            )
            return super().form_valid(form)
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Default success URL to detail view"""
        if hasattr(self, 'success_url') and self.success_url:
            return self.success_url
        return reverse(f'{self.model._meta.app_label}:{self.model._meta.model_name}_detail', 
                      kwargs={'pk': self.object.pk})


class BaseUpdateView(LoginRequiredMixin, StaffOrExtractorRequiredMixin, ServiceMixin, UpdateView):
    """Base update view using service"""
    
    def get_object(self):
        """Get object using service"""
        service = self.get_service()
        
        try:
            return service.get_object(self.kwargs['pk'])
        except ServiceException as e:
            self.handle_service_exception(e)
            return None
    
    def form_valid(self, form):
        """Handle form validation using service"""
        service = self.get_service()
        
        try:
            self.object = service.update(self.kwargs['pk'], form.cleaned_data)
            messages.success(
                self.request,
                _(f'{self.model._meta.verbose_name} atualizado com sucesso!')
            )
            return super().form_valid(form)
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.form_invalid(form)


class BaseDeleteView(LoginRequiredMixin, StaffOrExtractorRequiredMixin, ServiceMixin, DeleteView):
    """Base delete view using service (soft delete)"""
    
    def get_object(self):
        """Get object using service"""
        service = self.get_service()
        
        try:
            return service.get_object(self.kwargs['pk'])
        except ServiceException as e:
            self.handle_service_exception(e)
            return None
    
    def delete(self, request, *args, **kwargs):
        """Perform soft delete using service"""
        service = self.get_service()
        
        try:
            service.delete(self.kwargs['pk'])
            messages.success(
                self.request,
                _(f'{self.model._meta.verbose_name} excluído com sucesso!')
            )
            return JsonResponse({'success': True}) if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' else super().delete(request, *args, **kwargs)
        except ServiceException as e:
            self.handle_service_exception(e)
            return JsonResponse({'success': False, 'error': str(e)}) if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' else self.get(request, *args, **kwargs)


class SearchMixin:
    """Mixin for search functionality"""
    
    search_fields = []
    
    def get_search_query(self):
        """Get search query from request"""
        return self.request.GET.get('search', '').strip()
    
    def filter_queryset_by_search(self, queryset):
        """Filter queryset by search query"""
        query = self.get_search_query()
        if query and hasattr(queryset, 'search'):
            return queryset.search(query)
        return queryset


class ExportMixin:
    """Mixin for data export functionality"""
    
    export_formats = ['csv', 'xlsx', 'pdf']
    
    def get_export_format(self):
        """Get requested export format"""
        return self.request.GET.get('export', '').lower()
    
    def export_data(self, queryset, format_type):
        """Export data in specified format"""
        # Implementation depends on your export requirements
        pass


class BreadcrumbMixin:
    """Mixin for breadcrumb navigation"""
    
    breadcrumbs = []
    
    def get_breadcrumbs(self):
        """Get breadcrumbs for current view"""
        return self.breadcrumbs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context


class ExtractionUnitFilterMixin:
    """
    Mixin que filtra automaticamente queryset baseado nas 
    extraction_units do usuário extrator.
    
    Usuários extratores só podem acessar dados (extraction_request, cases e extractions) 
    das extraction_units às quais estão relacionados.
    
    Superusuários têm acesso a todos os dados.
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusuários veem tudo
        if user.is_superuser:
            return queryset
        
        # Verifica se é um usuário extrator
        try:
            # Busca todos os ExtractorUser vinculados ao usuário
            from apps.core.models import ExtractorUser
            
            extractor_users = ExtractorUser.objects.filter(
                user=user,
                deleted_at__isnull=True
            ).prefetch_related('extraction_unit_extractors')
            
            if not extractor_users.exists():
                # Não é um extrator, retorna queryset completo
                # (outras regras de permissão devem ser aplicadas)
                return queryset
            
            # Obtém todas as extraction_units vinculadas aos extractors do usuário
            extraction_unit_ids = []
            for extractor in extractor_users:
                unit_ids = extractor.extraction_unit_extractors.filter(
                    deleted_at__isnull=True
                ).values_list('extraction_unit_id', flat=True)
                extraction_unit_ids.extend(unit_ids)
            
            if not extraction_unit_ids:
                # Extrator sem unidades vinculadas, retorna queryset vazio
                return queryset.none()
            
            # Filtra o queryset pela extraction_unit
            # O campo pode variar dependendo do modelo
            if hasattr(queryset.model, 'extraction_unit'):
                return queryset.filter(extraction_unit__in=extraction_unit_ids)
            elif hasattr(queryset.model, 'case_device'):
                # Para Extraction model
                return queryset.filter(case_device__case__extraction_unit__in=extraction_unit_ids)
            
            return queryset
            
        except Exception as e:
            # Em caso de erro, retorna queryset vazio para segurança
            return queryset.none()