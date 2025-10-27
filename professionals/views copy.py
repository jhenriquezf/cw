"""
Views for professional search and filtering.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from professionals.models import Professional
from services.models import Service
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import CertificationForm
from django.contrib.auth.decorators import login_required
from .models import Certification
from django.apps import apps


def professional_search(request):
    """
    Main search view for professionals.
    Handles filtering by specialty, location, rating, modality, etc.
    """
    
    # Get query parameters
    search_query = request.GET.get('q', '')
    specialty = request.GET.get('specialty', '')
    comuna = request.GET.get('comuna', '')
    modality = request.GET.get('modality', '')
    service_type = request.GET.get('service_type', '')
    min_rating = request.GET.get('min_rating', '')
    
    # Base queryset - only verified and active professionals
    professionals = Professional.objects.filter(
        verification_status='verified',
        is_active=True
    ).select_related('user').prefetch_related('services', 'certifications')
    
    # Search filter (name or bio)
    if search_query:
        professionals = professionals.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(primary_specialty__icontains=search_query)
        )
    
    # Specialty filter
    if specialty:
        professionals = professionals.filter(primary_specialty=specialty)
    
    # Location filter
    if comuna:
        professionals = professionals.filter(comuna=comuna)
    
    # Rating filter
    if min_rating:
        try:
            min_rating_value = float(min_rating)
            professionals = professionals.filter(average_rating__gte=min_rating_value)
        except ValueError:
            pass
    
    # Modality filter (from services)
    if modality:
        professionals = professionals.filter(services__modality=modality).distinct()
    
    # Service type filter
    if service_type:
        professionals = professionals.filter(services__service_type=service_type).distinct()
    
    # Order by rating and bookings
    professionals = professionals.order_by('-average_rating', '-total_bookings')
    
    # Pagination
    paginator = Paginator(professionals, 12)  # 12 professionals per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for dropdowns
    context = {
        'page_obj': page_obj,
        'professionals': page_obj.object_list,
        'search_query': search_query,
        'selected_specialty': specialty,
        'selected_comuna': comuna,
        'selected_modality': modality,
        'selected_service_type': service_type,
        'selected_min_rating': min_rating,
        
        # Options for filters
        'specialties': Professional.PRIMARY_SPECIALTIES,
        'comunas': Professional.COMUNAS,
        'modalities': Service.MODALITIES,
        'service_types': Service.SERVICE_TYPES,
        'rating_options': [
            (4.5, '4.5+ stars'),
            (4.0, '4.0+ stars'),
            (3.5, '3.5+ stars'),
            (3.0, '3.0+ stars'),
        ],
        
        # Stats
        'total_results': paginator.count,
    }
    
    return render(request, 'professionals/search.html', context)


def professional_detail(request, username_slug):
    """
    Detail view for a specific professional.
    Shows profile, services, reviews, availability.
    """
    from django.shortcuts import get_object_or_404
    from reviews.models import Review
    
    professional = get_object_or_404(
        Professional.objects.select_related('user').prefetch_related(
            'services',
            'certifications',
            'reviews__client__user'
        ),
        username_slug=username_slug,
        is_active=True
    )
    
    # Get active services
    services = professional.services.filter(is_active=True)
    
    # Get approved reviews
    reviews = Review.objects.filter(
        professional=professional,
        is_approved=True
    ).select_related('client__user').order_by('-created_at')[:10]
    
    # Get verified certifications
    certifications = professional.certifications.filter(
        verification_status='verified'
    )
    
    context = {
        'professional': professional,
        'services': services,
        'reviews': reviews,
        'certifications': certifications,
    }
    
    return render(request, 'professionals/detail.html', context)


def featured_professionals(request):
    """
    Get featured professionals for homepage.
    Based on rating, bookings, and verification.
    """
    
    featured = Professional.objects.filter(
        verification_status='verified',
        is_active=True,
        average_rating__gte=4.5
    ).order_by('-average_rating', '-total_bookings')[:6]
    
    return {
        'featured_professionals': featured
    }

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ahora puedes iniciar sesión.')
            return redirect('login')  # Redirige al login después del registro exitoso
    else:
        form = UserCreationForm()
    # Asegúrate de tener una plantilla 'registration/register.html'
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

def professional_detail(request, username_slug):
    Professional = apps.get_model('professionals', 'Professional')
    prof = get_object_or_404(Professional, username_slug=username_slug)

    # Campos opcionales con defaults seguros
    def get_display(obj, field):
        try:
            # si es ChoiceField
            return getattr(obj, f"get_{field}_display")()
        except Exception:
            return getattr(obj, field, None)

    primary_specialty = None
    if hasattr(prof, "primary_specialty"):
        primary_specialty = get_display(prof, "primary_specialty")

    comuna = None
    if hasattr(prof, "comuna"):
        comuna = get_display(prof, "comuna")

    rating = getattr(prof, "average_rating", None)
    reviews = getattr(prof, "total_reviews", None)

    # Especializaciones (si tienes varios campos, ajústalo aquí)
    specializations_parts = []
    for fname in ("primary_specialty", "secondary_specialty", "tertiary_specialty"):
        if hasattr(prof, fname):
            val = get_display(prof, fname)
            if val:
                specializations_parts.append(str(val))
    specializations = ", ".join(dict.fromkeys([s for s in specializations_parts if s])) or None

    # Bio / about
    about_text = getattr(prof, "bio", None) or getattr(prof, "about", None) or ""

    # Certifications: solo verificadas si el modelo/field existe
    certifications = []
    try:
        Certification = apps.get_model('professionals', 'Certification')
        q = Certification.objects.filter(professional=prof)
        if hasattr(Certification, "verification_status"):
            q = q.filter(verification_status="verified")
        certifications = list(q.order_by("-year", "name"))
    except Exception:
        certifications = []

    # Gallery: usa URLs si existen campos (p.ej., photo de servicios o galería propia)
    gallery_images = []
    # 1) Intenta una relación Gallery/Image si existe
    if hasattr(prof, "gallery") and hasattr(prof.gallery, "all"):
        for g in prof.gallery.all():
            url = getattr(g, "image", None)
            if url:
                try:
                    gallery_images.append(url.url if hasattr(url, "url") else str(url))
                except Exception:
                    pass
    # 2) Si no hay, intenta imágenes de Services
    if not gallery_images:
        try:
            Service = apps.get_model('services', 'Service')
            for s in Service.objects.filter(professional=prof, is_active=True)[:9]:
                if hasattr(s, "image") and s.image:
                    gallery_images.append(s.image.url)
        except Exception:
            pass
    # 3) Si sigue vacío, deja vacío (el template muestra mensaje)

    ctx = {
        "prof": prof,
        "primary_specialty": primary_specialty,
        "comuna": comuna,
        "rating": rating,
        "reviews": reviews,
        "specializations": specializations,
        "about_text": about_text,
        "certifications": certifications,
        "gallery_images": gallery_images,
        "booking_url": "#",  # ajusta si tienes ruta de booking
    }
    return render(request, "professionals/detail.html", ctx)

def welcome_onboarding(request):
    return render(request, "professionals/welcome_onboarding.html")

def professional_search(request):
    q = (request.GET.get("q") or "").strip()

    qs = Professional.objects.select_related("user")
    if q:
        qs = qs.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(username_slug__icontains=q) |
            Q(primary_specialty__icontains=q)
        )

    paginator = Paginator(qs, 9)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    context = {
        "search_query": q,
        "professionals": page_obj.object_list,
        "page_obj": page_obj,
        "popular_terms": ["Pilates", "Yoga", "Nutrition", "Personal Training", "Meditation"],
    }
    return render(request, "professionals/search_results.html", context)