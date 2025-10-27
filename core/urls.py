# C:\Desarrollos\Procert\core\urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from professionals import views as professional_views # 👈 1. IMPORTA LAS VISTAS DE TU APP

urlpatterns = [
    path('admin/', admin.site.urls),
    path('profesionales/', include('professionals.urls')),
    
    # --- TUS URLS DE AUTENTICACIÓN ---
    path(
    'accounts/login/',
    auth_views.LoginView.as_view(template_name='professionals/login.html'),
    name='login'
),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', professional_views.register, name='register'), # 👈 2. AÑADE ESTA LÍNEA

    path('', RedirectView.as_view(url='/profesionales/', permanent=False), name='home'),
    path("i18n/", include("django.conf.urls.i18n")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)