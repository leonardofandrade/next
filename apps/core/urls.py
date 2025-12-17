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
]