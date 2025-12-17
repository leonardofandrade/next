"""
Views para o app core
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView, UpdateView

from django.db.models import Prefetch

from apps.core.models import ExtractionAgency, ExtractorUser, ExtractionUnitExtractor
from apps.core.forms import ExtractionAgencyForm


class ExtractionAgencyHubView(LoginRequiredMixin, TemplateView):
    """
    Página de configuração singleton da Agência de Extração.

    Não exige pk/slug na URL: carrega o primeiro (e idealmente único) registro.
    """

    template_name = 'core/extraction_agency_hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agency = ExtractionAgency.objects.prefetch_related('extraction_units').first()
        context['agency'] = agency
        context['extraction_units'] = (
            agency.extraction_units.all().order_by('acronym', 'name') if agency else []
        )

        if agency:
            extractor_users = ExtractorUser.objects.filter(
                extraction_agency=agency,
                deleted_at__isnull=True,
            ).select_related('user').prefetch_related(
                Prefetch(
                    'extraction_unit_extractors',
                    queryset=ExtractionUnitExtractor.objects.filter(
                        deleted_at__isnull=True,
                        extraction_unit__deleted_at__isnull=True,
                    ).select_related('extraction_unit').order_by('extraction_unit__acronym', 'extraction_unit__name'),
                    to_attr='active_unit_links',
                )
            ).order_by('user__first_name', 'user__last_name', 'user__username')
        else:
            extractor_users = []

        context['extractor_users'] = extractor_users
        return context


class ExtractionAgencyUpdateView(LoginRequiredMixin, UpdateView):
    """
    Tela de atualização (singleton) da Agência de Extração.

    Não usa PK na URL: sempre carrega o primeiro registro (e cria um vazio se não existir).
    """

    model = ExtractionAgency
    form_class = ExtractionAgencyForm
    template_name = 'core/extraction_agency_update.html'
    context_object_name = 'agency'

    def get_object(self, queryset=None):
        agency = ExtractionAgency.objects.first()
        if agency:
            return agency
        # Cria um registro placeholder para permitir edição posterior
        return ExtractionAgency.objects.create(acronym='', name='')

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('core:extraction_agency_hub')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Agência de extração atualizada com sucesso!'))
        return response