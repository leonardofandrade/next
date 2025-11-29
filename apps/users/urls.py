from django.urls import path
from apps.users import views

app_name = 'users'

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
]