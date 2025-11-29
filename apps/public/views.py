"""
Views para o app public
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy

from apps.public.forms import LoginForm


class LandingView(TemplateView):
    template_name = 'public/landing.html'
