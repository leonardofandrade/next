from django.urls import path
from apps.extractions import views

app_name = 'extractions'


urlpatterns = [
    path('', views.ExtractionListView.as_view(), name='list'),
    path('case/<int:pk>/', views.CaseExtractionsView.as_view(), name='case_extractions'),
    path('<int:pk>/assign-to-me/', views.ExtractionAssignToMeView.as_view(), name='assign_to_me'),
    path('<int:pk>/unassign-from-me/', views.ExtractionUnassignFromMeView.as_view(), name='unassign_from_me'),
]