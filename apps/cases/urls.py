from django.urls import path
from apps.cases import views

app_name = 'cases'

urlpatterns = [
    path('', views.CaseListView.as_view(), name='list'),
    path('<int:pk>/', views.CaseDetailView.as_view(), name='detail'),
    path('create/', views.CaseCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.CaseUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.CaseDeleteView.as_view(), name='delete'),
    path('<int:pk>/devices/', views.CaseDevicesView.as_view(), name='devices'),
    path('<int:pk>/devices/create-extractions/', views.CreateExtractionsView.as_view(), name='create_extractions'),
    path('<int:case_pk>/devices/create/', views.CaseDeviceCreateView.as_view(), name='device_create'),
    path('<int:case_pk>/devices/<int:pk>/update/', views.CaseDeviceUpdateView.as_view(), name='device_update'),
    path('<int:case_pk>/devices/<int:pk>/delete/', views.CaseDeviceDeleteView.as_view(), name='device_delete'),
]