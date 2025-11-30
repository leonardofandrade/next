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
]