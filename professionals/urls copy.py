"""
URLs for professionals app.
"""

from django.urls import path
from . import views

app_name = 'professionals'

urlpatterns = [
    # Search/Browse professionals
    path('', views.professional_search, name='search'),
    path('search/', views.professional_search, name='search_alias'),
    path('onboarding/certifications/', views.onboarding_certifications, name='onboarding_certifications'),
    path("onboarding/welcome/", views.welcome_onboarding, name="welcome_onboarding"),
    path('<slug:username_slug>/', views.professional_detail, name='detail'),
]