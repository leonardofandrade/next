from django.urls import path
from apps.cases import views

app_name = 'cases'

urlpatterns = [
    path('', views.case_list, name='list'),
    path('<int:pk>/', views.case_detail, name='detail'),
    path('create/', views.case_create, name='create'),
    path('<int:pk>/update/', views.case_update, name='update'),
    path('<int:pk>/delete/', views.case_delete, name='delete'),
    path('<int:pk>/devices/', views.case_devices, name='devices'),
    path('<int:case_pk>/devices/create/', views.case_device_create, name='device_create'),
    path('<int:case_pk>/devices/<int:device_pk>/update/', views.case_device_update, name='device_update'),
    path('<int:case_pk>/devices/<int:device_pk>/delete/', views.case_device_delete, name='device_delete'),
]