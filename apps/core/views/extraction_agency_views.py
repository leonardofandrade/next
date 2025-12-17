"""
Views para o app core
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.core.models import ExtractionAgency


class ExtractionAgencyHirearchyView(LoginRequiredMixin, TemplateView):
    """
    Página de configuração singleton da Agência de Extração.

    Não exige pk/slug na URL: carrega o primeiro (e idealmente único) registro.
    """

    template_name = 'core/extraction_agency_hirearchy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency'] = ExtractionAgency.objects.first()
        return context