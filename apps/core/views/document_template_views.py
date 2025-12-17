"""
Views para gerenciar templates de ofícios
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from apps.core.models import ExtractionUnit, DocumentTemplate
from apps.core.forms import DocumentTemplateForm
from apps.core.mixins.views import StaffRequiredMixin


class DocumentTemplateCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Cria novo template de ofício"""
    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'core/document_template_form.html'

    def _get_safe_next_url(self):
        next_url = (self.request.POST.get('next') or self.request.GET.get('next') or '').strip()
        if not next_url:
            return None
        if url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return None

    def get_initial(self):
        initial = super().get_initial()
        unit_id = (self.request.GET.get('extraction_unit') or '').strip()
        if unit_id:
            try:
                initial['extraction_unit'] = ExtractionUnit.objects.get(pk=unit_id, deleted_at__isnull=True)
            except ExtractionUnit.DoesNotExist:
                pass
        return initial

    def get_success_url(self):
        # Fallback: volta para o hub (aba templates) da unidade do template criado
        unit_id = getattr(self.object, 'extraction_unit_id', None)
        if unit_id:
            return f"{reverse('core:extraction_unit_hub')}?unit={unit_id}&tab=templates"
        return reverse('core:extraction_unit_hub')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Novo Template'
        context['next_url'] = self._get_safe_next_url()
        context['fallback_url'] = self.get_success_url()
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Template criado com sucesso!')
        response = super().form_valid(form)
        next_url = self._get_safe_next_url()
        return redirect(next_url) if next_url else response


class DocumentTemplateUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Atualiza template de documento"""
    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'core/document_template_form.html'

    def _get_safe_next_url(self):
        next_url = (self.request.POST.get('next') or self.request.GET.get('next') or '').strip()
        if not next_url:
            return None
        if url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return None

    def get_success_url(self):
        unit_id = getattr(self.object, 'extraction_unit_id', None)
        if unit_id:
            return f"{reverse('core:extraction_unit_hub')}?unit={unit_id}&tab=templates"
        return reverse('core:extraction_unit_hub')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Template'
        context['next_url'] = self._get_safe_next_url()
        context['fallback_url'] = self.get_success_url()
        return context
    
    def get_queryset(self):
        return DocumentTemplate.objects.filter(deleted_at__isnull=True)
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Template atualizado com sucesso!')
        response = super().form_valid(form)
        next_url = self._get_safe_next_url()
        return redirect(next_url) if next_url else response


class DocumentTemplateDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """Remove template de ofício (soft delete)"""
    model = DocumentTemplate
    template_name = 'core/document_template_confirm_delete.html'

    def _get_safe_next_url(self):
        next_url = (self.request.POST.get('next') or self.request.GET.get('next') or '').strip()
        if not next_url:
            return None
        if url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return None

    def get_success_url(self):
        unit_id = getattr(self.object, 'extraction_unit_id', None)
        if unit_id:
            return f"{reverse('core:extraction_unit_hub')}?unit={unit_id}&tab=templates"
        return reverse('core:extraction_unit_hub')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = self._get_safe_next_url()
        context['fallback_url'] = self.get_success_url()
        return context
    
    def get_queryset(self):
        return DocumentTemplate.objects.filter(deleted_at__isnull=True)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted_at = timezone.now()
        self.object.updated_by = request.user
        self.object.save()
        messages.success(request, 'Template removido com sucesso!')
        next_url = self._get_safe_next_url()
        return redirect(next_url) if next_url else redirect(self.get_success_url())


class DocumentTemplateDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """Visualiza detalhes do template"""
    model = DocumentTemplate
    template_name = 'core/document_template_detail.html'
    context_object_name = 'template'

    def _get_safe_next_url(self):
        next_url = (self.request.GET.get('next') or '').strip()
        if not next_url:
            return None
        if url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = self._get_safe_next_url()
        unit_id = getattr(self.object, 'extraction_unit_id', None)
        context['fallback_url'] = f"{reverse('core:extraction_unit_hub')}?unit={unit_id}&tab=templates" if unit_id else reverse('core:extraction_unit_hub')
        return context
    
    def get_queryset(self):
        return DocumentTemplate.objects.filter(deleted_at__isnull=True)


class DocumentTemplateDownloadView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
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
