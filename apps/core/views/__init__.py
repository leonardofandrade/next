from apps.core.views.extraction_agency_views import (
    ExtractionAgencyHubView,
    ExtractionAgencyUpdateView,
)
from apps.core.views.extraction_unit_views import (
    ExtractionUnitHubView,
    ExtractionUnitUpdateView,
    ExtractionUnitReplyEmailUpdateView,
)
from apps.core.views.document_template_views import (
    DocumentTemplateHubView,
    DocumentTemplateCreateView,
    DocumentTemplateUpdateView,
)
from apps.core.views.extractor_user_views import (
    ExtractorUserCreateView,
    ExtractorUserUpdateView,
    ExtractorUserUnitsAjaxView,
)

__all__ = [
    'ExtractionAgencyHubView',
    'ExtractionAgencyUpdateView',
    'ExtractionUnitHubView',
    'ExtractionUnitUpdateView',
    'ExtractionUnitReplyEmailUpdateView',
    'DocumentTemplateHubView',
    'DocumentTemplateCreateView',
    'DocumentTemplateUpdateView',
    'ExtractorUserCreateView',
    'ExtractorUserUpdateView',
    'ExtractorUserUnitsAjaxView',
]