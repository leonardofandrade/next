from django.urls import path
from . import views
from .views.document_template_views import (
    DocumentTemplateListView,
    DocumentTemplateCreateView,
    DocumentTemplateDetailView,
    DocumentTemplateUpdateView,
    DocumentTemplateDeleteView,
    DocumentTemplateDownloadView,
)

app_name = 'core'

urlpatterns = [
    # Extraction Agency URLs
    path('agencies/', views.extraction_agency_list, name='extraction_agency_list'),
    path('agencies/create/', views.extraction_agency_create, name='extraction_agency_create'),
    path('agencies/graph/', views.extraction_agency_graph, name='extraction_agency_graph'),
    path('agencies/<int:pk>/', views.extraction_agency_detail, name='extraction_agency_detail'),
    path('agencies/<int:pk>/edit/', views.extraction_agency_edit, name='extraction_agency_edit'),
    path('agencies/<int:pk>/delete/', views.extraction_agency_delete, name='extraction_agency_delete'),
    
    # Extraction Unit URLs
    path('units/', views.extraction_unit_list, name='extraction_unit_list'),
    path('units/create/', views.extraction_unit_create, name='extraction_unit_create'),
    path('units/<int:pk>/', views.extraction_unit_detail, name='extraction_unit_detail'),
    path('units/<int:pk>/edit/', views.extraction_unit_edit, name='extraction_unit_edit'),
    path('units/<int:pk>/delete/', views.extraction_unit_delete, name='extraction_unit_delete'),
    
    # Extractor User URLs
    path('extractors/', views.extractor_user_list, name='extractor_user_list'),
    path('extractors/create/', views.extractor_user_create, name='extractor_user_create'),
    path('extractors/<int:pk>/delete/', views.extractor_user_delete, name='extractor_user_delete'),
    
    # Extraction Unit Extractor URLs
    path('extraction-unit-extractors/', views.extraction_unit_extractor_list, name='extraction_unit_extractor_list'),
    path('extraction-unit-extractors/create/', views.extraction_unit_extractor_create, name='extraction_unit_extractor_create'),
    path('extraction-unit-extractors/<int:pk>/delete/', views.extraction_unit_extractor_delete, name='extraction_unit_extractor_delete'),
    
    # Storage Media URLs
    path('storage-media/', views.storage_media_list, name='storage_media_list'),
    path('storage-media/create/', views.storage_media_create, name='storage_media_create'),
    path('storage-media/<int:pk>/edit/', views.storage_media_edit, name='storage_media_edit'),
    path('storage-media/<int:pk>/delete/', views.storage_media_delete, name='storage_media_delete'),
    
    # Evidence Location URLs
    path('evidence-locations/', views.evidence_location_list, name='evidence_location_list'),
    path('evidence-locations/create/', views.evidence_location_create, name='evidence_location_create'),
    path('evidence-locations/<int:pk>/edit/', views.evidence_location_edit, name='evidence_location_edit'),
    path('evidence-locations/<int:pk>/delete/', views.evidence_location_delete, name='evidence_location_delete'),
    
    # Settings URLs
    path('settings/general/', views.general_settings, name='general_settings'),
    path('settings/email/', views.email_settings, name='email_settings'),
    path('settings/reports/', views.reports_settings, name='reports_settings'),
    
    # User Extractor Management URLs
    path('user-extractor-management/', views.user_extractor_management, name='user_extractor_management'),
    path('user-extractor-management/user/<int:user_id>/toggle-extractor/', views.toggle_extractor, name='toggle_extractor'),
    path('user-extractor-management/extractor/<int:extractor_user_id>/toggle-unit/', views.toggle_unit_association, name='toggle_unit_association'),
    path('user-extractor-management/extractor/<int:extractor_user_id>/associate-all-units/', views.associate_all_units, name='associate_all_units'),
    path('user-extractor-management/user/<int:user_id>/info/', views.get_user_extractor_info, name='get_user_extractor_info'),
    
    # Document Template URLs
    path('document-templates/', DocumentTemplateListView.as_view(), name='document_template_list'),
    path('document-templates/create/', DocumentTemplateCreateView.as_view(), name='document_template_create'),
    path('document-templates/<int:pk>/', DocumentTemplateDetailView.as_view(), name='document_template_detail'),
    path('document-templates/<int:pk>/edit/', DocumentTemplateUpdateView.as_view(), name='document_template_update'),
    path('document-templates/<int:pk>/delete/', DocumentTemplateDeleteView.as_view(), name='document_template_delete'),
    path('document-templates/<int:pk>/download/', DocumentTemplateDownloadView.as_view(), name='document_template_download'),
]