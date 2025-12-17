"""
Views para DocumentTemplate (templates de ofício) por ExtractionUnit.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView, CreateView, UpdateView

from apps.core.models import ExtractionUnit, DocumentTemplate
from apps.core.forms import DocumentTemplateForm


class DocumentTemplateHubView(LoginRequiredMixin, TemplateView):
    """
    Hub/lista de templates de documento (ofício) para uma ExtractionUnit.
    """

    template_name = 'core/document_template_hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            unit = ExtractionUnit.objects.get(pk=self.kwargs['unit_pk'])
        except ExtractionUnit.DoesNotExist as exc:
            raise Http404('Unidade de extração não encontrada.') from exc

        templates = unit.document_templates.all().order_by('-is_default', 'name')

        context['unit'] = unit
        context['templates'] = templates
        return context


class DocumentTemplateCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um template de documento para uma ExtractionUnit.
    """

    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'core/document_template_form.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.unit = ExtractionUnit.objects.get(pk=self.kwargs['unit_pk'])
        except ExtractionUnit.DoesNotExist as exc:
            raise Http404('Unidade de extração não encontrada.') from exc
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.extraction_unit = self.unit
        response = super().form_valid(form)
        messages.success(self.request, _('Template de documento criado com sucesso!'))
        return response

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('core:document_template_hub', kwargs={'unit_pk': self.unit.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unit'] = self.unit
        context['page_title'] = _('Novo Template de Documento')
        return context


class DocumentTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza um template de documento (garante que pertence à unidade na URL).
    """

    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'core/document_template_form.html'
    context_object_name = 'template'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.extraction_unit_id != self.kwargs['unit_pk']:
            raise Http404('Template não pertence à unidade informada.')
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Template de documento atualizado com sucesso!'))
        return response

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('core:document_template_hub', kwargs={'unit_pk': self.kwargs['unit_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unit'] = self.object.extraction_unit
        context['page_title'] = _('Editar Template de Documento')
        return context

