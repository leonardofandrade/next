from django.urls import path
from apps.extractions import views

app_name = 'extractions'


urlpatterns = [
    path('case/<int:pk>/', views.CaseExtractionsView.as_view(), name='case_extractions'),
]