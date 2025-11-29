from django.urls import path
from apps.requisitions import views

app_name = 'requisitions'

urlpatterns = [
    path('', views.extraction_request_list, name='list'),
    path('not-received/', views.extraction_request_not_received, name='not_received'),
    path('<int:pk>/', views.extraction_request_detail, name='detail'),
    path('create/', views.extraction_request_create, name='create'),
    path('<int:pk>/update/', views.extraction_request_update, name='update'),
    path('<int:pk>/delete/', views.extraction_request_delete, name='delete'),
]