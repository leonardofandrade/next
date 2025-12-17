from django.urls import path
from apps.core import views

app_name = 'core'

urlpatterns = [
    # ExtractionAgency (singleton)
    path('settings/extraction-agency/', views.ExtractionAgencyHirearchyView.as_view(), name='extraction_agency_hirearchy'),

]