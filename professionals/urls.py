# professionals/urls.py

from django.urls import path
from . import views

app_name = 'professionals'

urlpatterns = [
    # The root path '/' is your main landing page
    path('', views.landing, name='home'),
    
    # Login and Signup URLs
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("signup/", views.UserRegistrationView.as_view(), name="signup"),
    
    # The search page now lives at '/search/'
    path("search/", views.search_page, name="search"),
    
    # The search results page
    path('results/', views.search_results, name='search_results'),
    
    # Onboarding URLs
    path('onboarding/certifications/', views.onboarding_certifications, name='onboarding_certifications'),
    
    # Professional detail page
    path('<slug:username_slug>/', views.professional_detail, name='detail'),
]