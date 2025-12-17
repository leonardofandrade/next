from django.urls import path
from apps.core import views

app_name = 'core'

urlpatterns = [
    # ExtractionAgency (singleton)
    path('settings/extraction-agency/', views.ExtractionAgencyHubView.as_view(), name='extraction_agency_hub'),
    path('settings/extraction-agency/edit/', views.ExtractionAgencyUpdateView.as_view(), name='extraction_agency_update'),

    # ExtractionUnit
    path('settings/extraction-units/<int:pk>/', views.ExtractionUnitHubView.as_view(), name='extraction_unit_hub'),
    path('settings/extraction-units/<int:pk>/edit/', views.ExtractionUnitUpdateView.as_view(), name='extraction_unit_update'),
    path('settings/extraction-units/<int:pk>/email-template/', views.ExtractionUnitReplyEmailUpdateView.as_view(), name='extraction_unit_reply_email_update'),

    # DocumentTemplate (por ExtractionUnit)
    path('settings/extraction-units/<int:unit_pk>/document-templates/', views.DocumentTemplateHubView.as_view(), name='document_template_hub'),
    path('settings/extraction-units/<int:unit_pk>/document-templates/new/', views.DocumentTemplateCreateView.as_view(), name='document_template_create'),
    path('settings/extraction-units/<int:unit_pk>/document-templates/<int:pk>/edit/', views.DocumentTemplateUpdateView.as_view(), name='document_template_update'),

    # ExtractorUser (gerenciamento no hub da agência)
    path('settings/extraction-agency/extractors/new/', views.ExtractorUserCreateView.as_view(), name='extractor_user_create'),
    path('settings/extraction-agency/extractors/<int:pk>/edit/', views.ExtractorUserUpdateView.as_view(), name='extractor_user_update'),
    path('settings/extraction-agency/extractors/ajax/units/', views.ExtractorUserUnitsAjaxView.as_view(), name='extractor_user_units_ajax'),
]