from django.urls import path
from apps.core import views

app_name = 'core'

urlpatterns = [
    # ExtractionAgency (singleton)
    path('settings/extraction-agency/', views.ExtractionAgencyHubView.as_view(), name='extraction_agency_hub'),

]