"""
Views para o app cases - Pacote modularizado

Este pacote contém todas as views organizadas por funcionalidade:
- case_views.py: Views relacionadas ao modelo Case
- case_device_views.py: Views relacionadas ao modelo CaseDevice
- case_procedure_views.py: Views relacionadas ao modelo CaseProcedure
"""
# Importa views relacionadas ao modelo Case
from apps.cases.views.case_views import (
    CaseListView,
    CaseWaitingExtractorListView,
    CaseDetailView,
    CaseHubView,
    CaseCreateView,
    CaseUpdateView,
    CaseUpdateFullView,
    CaseDeleteView,
    CaseCompleteRegistrationView,
    CaseDevicesView,
    CaseProceduresView,
    CaseDocumentsView,
    CreateExtractionsView,
    CaseAssignToMeView,
    CaseUnassignFromMeView,
    CaseCoverPDFView,
)
from apps.cases.views.case_cover_odt_view import (
    CaseCoverODTView,
    CaseDispatchGenerateView,
    CaseDispatchDownloadView,
)

# Importa views relacionadas ao modelo CaseDevice
from apps.cases.views.case_device_views import (
    CaseDeviceCreateView,
    CaseDeviceUpdateView,
    CaseDeviceDetailView,
    CaseDeviceDeleteView,
    CaseDeviceFormModalView,
)

# Importa views relacionadas ao modelo CaseProcedure
from apps.cases.views.case_procedure_views import (
    CaseProcedureCreateView,
    CaseProcedureDetailView,
    CaseProcedureUpdateView,
    CaseProcedureDeleteView,
)

# Importa views relacionadas ao modelo CaseDocument
from apps.cases.views.case_document_views import (
    CaseDocumentCreateView,
    CaseDocumentDetailView,
    CaseDocumentUpdateView,
    CaseDocumentDeleteView,
)

# Exporta todas as views para manter compatibilidade
__all__ = [
    # Case views
    'CaseListView',
    'CaseWaitingExtractorListView',
    'CaseDetailView',
    'CaseHubView',
    'CaseCreateView',
    'CaseUpdateView',
    'CaseUpdateFullView',
    'CaseDeleteView',
    'CaseCompleteRegistrationView',
    'CaseDevicesView',
    'CaseProceduresView',
    'CaseDocumentsView',
    'CreateExtractionsView',
    'CaseAssignToMeView',
    'CaseUnassignFromMeView',
    'CaseCoverPDFView',
    'CaseCoverODTView',
    'CaseDispatchGenerateView',
    'CaseDispatchDownloadView',
    # CaseDevice views
    'CaseDeviceCreateView',
    'CaseDeviceUpdateView',
    'CaseDeviceDetailView',
    'CaseDeviceDeleteView',
    'CaseDeviceFormModalView',
    # CaseProcedure views
    'CaseProcedureCreateView',
    'CaseProcedureDetailView',
    'CaseProcedureUpdateView',
    'CaseProcedureDeleteView',
    # CaseDocument views
    'CaseDocumentCreateView',
    'CaseDocumentDetailView',
    'CaseDocumentUpdateView',
    'CaseDocumentDeleteView',
]

