"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def redirect_to_next(request):
    """Redireciona automaticamente para /next/"""
    return redirect('/next/')

urlpatterns = [
    path('', redirect_to_next),
    path('next/', include([
        path('admin/', admin.site.urls),
        path('', include('apps.public.urls')),
        path('tables/', include('apps.base_tables.urls')),
        path('user', include('apps.users.urls')),
        path('', include('apps.core.urls')),
        path('requisitions/', include('apps.requisitions.urls')),
    ])),
]
