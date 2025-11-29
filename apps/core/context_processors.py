"""
Context processors para o app core.
Disponibiliza dados globais para todos os templates.
"""
from apps.core.models import ExtractionAgency


def extraction_agency(request):
    """
    Adiciona informações da agência de extração ao contexto.
    Disponível em todos os templates como {{ extraction_agency }}.
    """
    try:
        # Busca a primeira (e única) agência de extração
        agency = ExtractionAgency.objects.first()
        return {
            'extraction_agency': agency,
        }
    except Exception:
        return {
            'extraction_agency': None,
        }
