"""
Views for professional search, filtering, and profiles.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from professionals.models import Professional, Certification
from services.models import Service
from reviews.models import Review
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import CertificationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.views import View
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

# NOTA: El import 'from django.apps import apps' fue eliminado ya que no se utiliza en esta versión unificada.

# --- Vistas de Búsqueda y Navegación ---

def search_page(request):
    """
    Renderiza la página de búsqueda inicial (search.html).
    Esta vista también obtiene y muestra una lista de profesionales destacados.
    """
    featured_professionals = Professional.objects.filter(
        verification_status='verified',
        is_active=True,
        average_rating__gte=4.5
    ).order_by('-average_rating', '-total_bookings')[:6]

    context = {
        'featured_professionals': featured_professionals,
    }
    return render(request, 'professionals/search.html', context)


def search_results(request):
    """
    Maneja la lógica de búsqueda y filtrado y renderiza la página de resultados.
    Esta es una fusión completa de las dos funciones `professional_search` originales.
    """
    # --- Obtención de TODOS los parámetros de la URL ---
    search_query = request.GET.get('q', '').strip()
    specialty = request.GET.get('specialty', '')
    comuna = request.GET.get('comuna', '')
    modality = request.GET.get('modality', '')
    service_type = request.GET.get('service_type', '')
    min_rating = request.GET.get('min_rating', '')

    # --- Queryset Base ---
    professionals = Professional.objects.filter(
        verification_status='verified', is_active=True
    ).select_related('user').prefetch_related('services', 'certifications')

    # --- Aplicación de Filtros (combinando ambas lógicas) ---
    if search_query:
        professionals = professionals.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(primary_specialty__icontains=search_query) |
            Q(username_slug__icontains=search_query)
        ).distinct()

    if specialty:
        professionals = professionals.filter(primary_specialty=specialty)
    
    if comuna:
        professionals = professionals.filter(comuna=comuna)

    if modality:
        professionals = professionals.filter(services__modality=modality).distinct()

    if service_type:
        professionals = professionals.filter(services__service_type=service_type).distinct()

    if min_rating:
        try:
            min_rating_value = float(min_rating)
            professionals = professionals.filter(average_rating__gte=min_rating_value)
        except (ValueError, TypeError):
            pass

    # --- Ordenamiento ---
    professionals = professionals.order_by('-average_rating', '-total_bookings')

    # --- Paginación ---
    paginator = Paginator(professionals, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # --- Contexto Completo para la Plantilla ---
    context = {
        'page_obj': page_obj,
        'professionals': page_obj.object_list,
        'total_results': paginator.count,
        'search_query': search_query,
        'popular_terms': ["Pilates", "Yoga", "Nutrition", "Personal Training", "Meditation"],
        'selected_specialty': specialty,
        'selected_comuna': comuna,
        'selected_modality': modality,
        'selected_service_type': service_type,
        'selected_min_rating': min_rating,
        'specialties': Professional.PRIMARY_SPECIALTIES,
        'comunas': Professional.COMUNAS,
        'modalities': Service.MODALITIES,
        'service_types': Service.SERVICE_TYPES,
        'rating_options': [
            (4.5, '4.5+ estrellas'), (4.0, '4.0+ estrellas'),
            (3.5, '3.5+ estrellas'), (3.0, '3.0+ estrellas'),
        ],
    }
    return render(request, 'professionals/search_results.html', context)


def professional_detail(request, username_slug):
    """
    Muestra el perfil detallado de un profesional (versión unificada y corregida).
    """
    professional = get_object_or_404(
        Professional.objects.select_related('user'),
        username_slug=username_slug,
        is_active=True
    )

    # --- Obtener datos relacionados de forma optimizada ---
    services = professional.services.filter(is_active=True)
    reviews = Review.objects.filter(professional=professional, is_approved=True).select_related('client__user').order_by('-created_at')[:10]
    certifications = professional.certifications.filter(verification_status='verified').order_by("-year", "name")

    # --- Lógica para obtener campos de forma segura (de la segunda función original) ---
    about_text = getattr(professional, "bio", None) or getattr(professional, "about", None) or ""

    # --- Lógica para la galería de imágenes (corregida y optimizada) ---
    gallery_images = []
    for s in services:
        if hasattr(s, "image") and s.image:
            try:
                gallery_images.append(s.image.url)
            except Exception:
                pass
    
    # --- Contexto Unificado para la Plantilla ---
    # CORRECCIÓN: Se estandariza el nombre de la variable principal a 'professional'
    context = {
        'professional': professional,
        'services': services,
        'reviews': reviews,
        'certifications': certifications,
        'about_text': about_text,
        'gallery_images': gallery_images,
    }
    return render(request, "professionals/detail.html", context)


# --- Vistas de Registro y Onboarding (Sin cambios funcionales, solo validación) ---

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def onboarding_certifications(request):
    prof = request.user.professional_profile  # related_name en Professional
    if request.method == 'POST':
        # Borrar certificación
        if 'delete_id' in request.POST:
            cert = get_object_or_404(Certification, pk=request.POST['delete_id'], professional=prof)
            cert.delete()
            messages.success(request, 'Certificación eliminada.')
            return redirect('professionals:onboarding_certifications')

        # Agregar certificación
        form = CertificationForm(request.POST, request.FILES)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.professional = prof
            # Queda con verification_status='pending_review' por defecto en el modelo
            cert.save()
            messages.success(request, 'Certificación agregada. Quedará pendiente de verificación.')
            return redirect('professionals:onboarding_certifications')
    else:
        form = CertificationForm()

    certifications = prof.certifications.all().order_by('-year', '-created_at')
    return render(request, 'professionals/onboarding_certifications.html', {
        'form': form,
        'certifications': certifications,
    })


def landing(request):
    # Página de inicio
    return render(request, "professionals/welcome_onboarding.html")

class UserLoginView(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'professionals/Login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('professionals:home')  # Redirige después del login
        return render(request, 'professionals/Login.html', {'form': form})

class UserRegistrationView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'professionals/signup.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            if user is not None:
                login(request, user)
                return redirect('professionals:home')
        return render(request, 'professionals/signup.html', {'form': form})