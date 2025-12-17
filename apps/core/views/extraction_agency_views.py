"""
Views para o app core
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.core.models import ExtractionAgency


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
        return context