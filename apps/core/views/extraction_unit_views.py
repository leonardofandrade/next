"""
Views para ExtractionUnit (app core)
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView, UpdateView

from apps.core.models import ExtractionUnit, ExtractionUnitReportSettings
from apps.core.forms import ExtractionUnitForm, ExtractionUnitReplyEmailForm, ExtractionUnitReportSettingsForm


class ExtractionUnitHubView(LoginRequiredMixin, TemplateView):
    """
    Página hub (detail) da Unidade de Extração.

    Por enquanto, exibe os dados e permite navegar para edição.
    """

    template_name = 'core/extraction_unit_hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            unit = ExtractionUnit.objects.select_related('agency').get(pk=self.kwargs['pk'])
        except ExtractionUnit.DoesNotExist as exc:
            raise Http404('Unidade de extração não encontrada.') from exc

        context['unit'] = unit
        return context


class ExtractionUnitUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualização de uma Unidade de Extração.
    """

    model = ExtractionUnit
    form_class = ExtractionUnitForm
    template_name = 'core/extraction_unit_update.html'
    context_object_name = 'unit'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('core:extraction_unit_hub', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Unidade de extração atualizada com sucesso!'))
        return response


class ExtractionUnitReplyEmailUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza apenas os campos de template de e-mail de resposta da unidade.
    """

    model = ExtractionUnit
    form_class = ExtractionUnitReplyEmailForm
    template_name = 'core/extraction_unit_reply_email_update.html'
    context_object_name = 'unit'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('core:extraction_unit_hub', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Template de e-mail atualizado com sucesso!'))
        return response


class ExtractionUnitReportSettingsUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza as configurações de relatórios da unidade.
    Cria o registro se não existir.
    """

    model = ExtractionUnitReportSettings
    form_class = ExtractionUnitReportSettingsForm
    template_name = 'core/extraction_unit_report_settings_update.html'
    context_object_name = 'report_settings'

    def get_object(self, queryset=None):
        """Obtém ou cria o objeto de configurações de relatórios"""
        unit = ExtractionUnit.objects.get(pk=self.kwargs['pk'])
        report_settings, created = ExtractionUnitReportSettings.objects.get_or_create(
            extraction_unit=unit,
            defaults={'reports_enabled': True}
        )
        return report_settings

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('core:extraction_unit_hub', kwargs={'pk': self.object.extraction_unit.pk})

    def form_valid(self, form):
        # Garante que o extraction_unit está definido
        if not form.instance.extraction_unit_id:
            form.instance.extraction_unit_id = self.kwargs['pk']
        response = super().form_valid(form)
        messages.success(self.request, _('Configurações de relatórios atualizadas com sucesso!'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unit'] = self.object.extraction_unit
        return context
