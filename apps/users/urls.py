from django.urls import path
from apps.users import views
from apps.users.views.extractor_views import MyCasesView, MyExtractionsView, extractor_home_view

app_name = 'users'

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('extractor-home/', extractor_home_view, name='extractor_home'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/image/<int:pk>/', views.profile_image, name='profile_image'),
    path('my-cases/', MyCasesView.as_view(), name='my_cases'),
    path('my-extractions/', MyExtractionsView.as_view(), name='my_extractions'),
]