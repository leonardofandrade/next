from django.urls import path
from apps.extractions import views

app_name = 'extractions'


urlpatterns = [
    path('', views.ExtractionListView.as_view(), name='list'),
    path('case/<int:pk>/', views.CaseExtractionsView.as_view(), name='case_extractions'),
]