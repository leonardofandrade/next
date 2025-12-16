"""
Views para gerenciar templates de ofícios
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone

from apps.core.models import ExtractionUnit, DispatchTemplate
from apps.core.forms import DispatchTemplateForm


class DispatchTemplateListView(LoginRequiredMixin, ListView):
    """Lista templates de ofícios"""
    model = DispatchTemplate
    template_name = 'core/oficio_template_list.html'
    context_object_name = 'templates'
    
    def get_queryset(self):
        queryset = DispatchTemplate.objects.filter(deleted_at__isnull=True)
        
        # Filtro por extraction_unit se fornecido
        extraction_unit_id = self.request.GET.get('extraction_unit')
        if extraction_unit_id:
            queryset = queryset.filter(extraction_unit_id=extraction_unit_id)
        
        return queryset.select_related('extraction_unit')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extraction_units'] = ExtractionUnit.objects.filter(deleted_at__isnull=True)
        return context


class DispatchTemplateCreateView(LoginRequiredMixin, CreateView):
    """Cria novo template de ofício"""
    model = DispatchTemplate
    form_class = DispatchTemplateForm
    template_name = 'core/dispatch_template_form.html'
    success_url = reverse_lazy('core:dispatch_template_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Template criado com sucesso!')
        return super().form_valid(form)


class DispatchTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Atualiza template de ofício"""
    model = DispatchTemplate
    form_class = DispatchTemplateForm
    template_name = 'core/dispatch_template_form.html'
    success_url = reverse_lazy('core:dispatch_template_list')
    
    def get_queryset(self):
        return DispatchTemplate.objects.filter(deleted_at__isnull=True)
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Template atualizado com sucesso!')
        return super().form_valid(form)


class DispatchTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Remove template de ofício (soft delete)"""
    model = DispatchTemplate
    template_name = 'core/dispatch_template_confirm_delete.html'
    success_url = reverse_lazy('core:dispatch_template_list')
    
    def get_queryset(self):
        return DispatchTemplate.objects.filter(deleted_at__isnull=True)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted_at = timezone.now()
        self.object.updated_by = request.user
        self.object.save()
        messages.success(request, 'Template removido com sucesso!')
        return redirect(self.success_url)


class DispatchTemplateDetailView(LoginRequiredMixin, DetailView):
    """Visualiza detalhes do template"""
    model = DispatchTemplate
    template_name = 'core/dispatch_template_detail.html'
    context_object_name = 'template'
    
    def get_queryset(self):
        return DispatchTemplate.objects.filter(deleted_at__isnull=True)


class DispatchTemplateDownloadView(LoginRequiredMixin, DetailView):
    """Download do arquivo template"""
    model = DispatchTemplate
    
    def get(self, request, *args, **kwargs):
        template = self.get_object()
        
        if not template.template_file:
            messages.error(request, 'Template não possui arquivo associado.')
            return redirect('core:dispatch_template_detail', pk=template.pk)
        
        response = HttpResponse(template.template_file, content_type='application/vnd.oasis.opendocument.text')
        filename = template.template_filename or f'template_{template.pk}.odt'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
