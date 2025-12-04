"""
Context processors para o app core.
Disponibiliza dados globais para todos os templates.
"""
from apps.core.models import ExtractionAgency, ExtractorUser


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


def is_extractor_user(request):
    """
    Verifica se o usuário logado é um extrator.
    Disponível em todos os templates como {{ is_extractor_user }}.
    """
    if not request.user.is_authenticated:
        return {
            'is_extractor_user': False,
        }
    
    try:
        ExtractorUser.objects.get(
            user=request.user,
            deleted_at__isnull=True
        )
        return {
            'is_extractor_user': True,
        }
    except ExtractorUser.DoesNotExist:
        return {
            'is_extractor_user': False,
        }
