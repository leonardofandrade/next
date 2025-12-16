"""
Services para o app cases - Pacote modularizado

Este pacote contém todos os services organizados por modelo:
- case_service.py: Service para o modelo Case
- case_device_service.py: Service para o modelo CaseDevice
- case_procedure_service.py: Service para o modelo CaseProcedure
- extraction_service.py: Service para o modelo Extraction
"""
# Importa services
from apps.cases.services.case_service import CaseService
from apps.cases.services.case_device_service import CaseDeviceService
from apps.cases.services.case_procedure_service import CaseProcedureService
from apps.cases.services.case_document_service import CaseDocumentService
from apps.cases.services.extraction_service import ExtractionService

# Exporta todos os services para manter compatibilidade
__all__ = [
    'CaseService',
    'CaseDeviceService',
    'CaseProcedureService',
    'CaseDocumentService',
    'ExtractionService',
]

