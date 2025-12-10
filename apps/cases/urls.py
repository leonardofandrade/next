from django.urls import path
from apps.cases import views

app_name = 'cases'

urlpatterns = [
    path('', views.CaseListView.as_view(), name='list'),
    path('<int:pk>/', views.CaseDetailView.as_view(), name='detail'),
    path('create/', views.CaseCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.CaseUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.CaseDeleteView.as_view(), name='delete'),
    path('<int:pk>/complete-registration/', views.CaseCompleteRegistrationView.as_view(), name='complete_registration'),
    path('<int:pk>/cover-pdf/', views.CaseCoverPDFView.as_view(), name='cover_pdf'),
    path('<int:pk>/assign-to-me/', views.CaseAssignToMeView.as_view(), name='assign_to_me'),
    path('<int:pk>/unassign-from-me/', views.CaseUnassignFromMeView.as_view(), name='unassign_from_me'),
    path('<int:pk>/devices/', views.CaseDevicesView.as_view(), name='devices'),
    path('<int:pk>/procedures/', views.CaseProceduresView.as_view(), name='procedures'),
    path('<int:pk>/devices/create-extractions/', views.CreateExtractionsView.as_view(), name='create_extractions'),
    path('<int:case_pk>/devices/create/', views.CaseDeviceCreateView.as_view(), name='device_create'),
    path('<int:case_pk>/devices/<int:pk>/', views.CaseDeviceDetailView.as_view(), name='device_detail'),
    path('<int:case_pk>/devices/<int:pk>/update/', views.CaseDeviceUpdateView.as_view(), name='device_update'),
    path('<int:case_pk>/devices/<int:pk>/form-modal/', views.CaseDeviceFormModalView.as_view(), name='device_form_modal'),
    path('<int:case_pk>/devices/<int:pk>/delete/', views.CaseDeviceDeleteView.as_view(), name='device_delete'),
    path('<int:case_pk>/procedures/create/', views.CaseProcedureCreateView.as_view(), name='procedure_create'),
    path('<int:case_pk>/procedures/<int:pk>/', views.CaseProcedureDetailView.as_view(), name='procedure_detail'),
    path('<int:case_pk>/procedures/<int:pk>/update/', views.CaseProcedureUpdateView.as_view(), name='procedure_update'),
    path('<int:case_pk>/procedures/<int:pk>/delete/', views.CaseProcedureDeleteView.as_view(), name='procedure_delete'),
]