from django.urls import path
from apps.public import views


app_name = 'public'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
]