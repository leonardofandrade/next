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

from apps.core.models import ExtractionUnit, DocumentTemplate
from apps.core.forms import DocumentTemplateForm


class DocumentTemplateListView(LoginRequiredMixin, ListView):
    """Lista templates de documentos"""
    model = DocumentTemplate
    template_name = 'core/document_template_list.html'
    context_object_name = 'templates'
    
    def get_queryset(self):
        queryset = DocumentTemplate.objects.filter(deleted_at__isnull=True)
        
        # Filtro por extraction_unit se fornecido
        extraction_unit_id = self.request.GET.get('extraction_unit')
        if extraction_unit_id:
            queryset = queryset.filter(extraction_unit_id=extraction_unit_id)
        
        return queryset.select_related('extraction_unit')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extraction_units'] = ExtractionUnit.objects.filter(deleted_at__isnull=True)
        return context


class DocumentTemplateCreateView(LoginRequiredMixin, CreateView):
    """Cria novo template de ofício"""
    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'core/document_template_form.html'
    success_url = reverse_lazy('core:document_template_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Template criado com sucesso!')
        return super().form_valid(form)


class DocumentTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Atualiza template de documento"""
    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'core/document_template_form.html'
    success_url = reverse_lazy('core:document_template_list')
    
    def get_queryset(self):
        return DocumentTemplate.objects.filter(deleted_at__isnull=True)
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Template atualizado com sucesso!')
        return super().form_valid(form)


class DocumentTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Remove template de ofício (soft delete)"""
    model = DocumentTemplate
    template_name = 'core/document_template_confirm_delete.html'
    success_url = reverse_lazy('core:document_template_list')
    
    def get_queryset(self):
        return DocumentTemplate.objects.filter(deleted_at__isnull=True)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted_at = timezone.now()
        self.object.updated_by = request.user
        self.object.save()
        messages.success(request, 'Template removido com sucesso!')
        return redirect(self.success_url)


class DocumentTemplateDetailView(LoginRequiredMixin, DetailView):
    """Visualiza detalhes do template"""
    model = DocumentTemplate
    template_name = 'core/document_template_detail.html'
    context_object_name = 'template'
    
    def get_queryset(self):
        return DocumentTemplate.objects.filter(deleted_at__isnull=True)


class DocumentTemplateDownloadView(LoginRequiredMixin, DetailView):
    """Download do documento gerado a partir do template"""
    model = DocumentTemplate
    
    def get(self, request, *args, **kwargs):
        template = self.get_object()
        
        # Verifica se há conteúdo no template
        if not (template.header_text or template.body_text or template.subject_text):
            messages.error(request, 'Template não possui conteúdo configurado.')
            return redirect('core:document_template_detail', pk=template.pk)
        
        # Para download, precisamos de um caso de exemplo ou gerar um documento genérico
        # Por enquanto, retorna erro informando que precisa de um caso
        messages.info(request, 'Para gerar o documento, use a funcionalidade de gerar ofício a partir de um caso.')
        return redirect('core:document_template_detail', pk=template.pk)
