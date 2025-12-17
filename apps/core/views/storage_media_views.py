"""
Views para ExtractionUnitStorageMedia (meios de armazenamento) por ExtractionUnit.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView, CreateView, UpdateView

from apps.core.models import ExtractionUnit, ExtractionUnitStorageMedia
from apps.core.forms import ExtractionUnitStorageMediaForm


class StorageMediaHubView(LoginRequiredMixin, TemplateView):
    """
    Hub/lista de meios de armazenamento para uma ExtractionUnit.
    """

    template_name = 'core/storage_media_hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            unit = ExtractionUnit.objects.get(pk=self.kwargs['unit_pk'])
        except ExtractionUnit.DoesNotExist as exc:
            raise Http404('Unidade de extração não encontrada.') from exc

        storage_medias = unit.storage_medias.filter(deleted_at__isnull=True).order_by('acronym', 'name')

        context['unit'] = unit
        context['storage_medias'] = storage_medias
        return context


class StorageMediaCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um meio de armazenamento para uma ExtractionUnit.
    """

    model = ExtractionUnitStorageMedia
    form_class = ExtractionUnitStorageMediaForm
    template_name = 'core/storage_media_form.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.unit = ExtractionUnit.objects.get(pk=self.kwargs['unit_pk'])
        except ExtractionUnit.DoesNotExist as exc:
            raise Http404('Unidade de extração não encontrada.') from exc
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.extraction_unit = self.unit
        response = super().form_valid(form)
        messages.success(self.request, _('Meio de armazenamento criado com sucesso!'))
        return response

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('core:storage_media_hub', kwargs={'unit_pk': self.unit.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unit'] = self.unit
        context['page_title'] = _('Novo Meio de Armazenamento')
        return context


class StorageMediaUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza um meio de armazenamento (garante que pertence à unidade na URL).
    """

    model = ExtractionUnitStorageMedia
    form_class = ExtractionUnitStorageMediaForm
    template_name = 'core/storage_media_form.html'
    context_object_name = 'storage_media'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.extraction_unit_id != self.kwargs['unit_pk']:
            raise Http404('Meio de armazenamento não pertence à unidade informada.')
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Meio de armazenamento atualizado com sucesso!'))
        return response

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('core:storage_media_hub', kwargs={'unit_pk': self.kwargs['unit_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unit'] = self.object.extraction_unit
        context['page_title'] = _('Editar Meio de Armazenamento')
        return context
