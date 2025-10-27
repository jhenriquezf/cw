"""
Models for the services app.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from professionals.models import Professional


class Service(models.Model):
    """
    Service offered by a professional.
    Example: "Vinyasa Yoga Individual", "Personal Training Session"
    """
    
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Profesional'
    )
    
    # Basic Info
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre del servicio',
        help_text='Ej: Clase de Vinyasa Yoga'
    )
    
    description = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del servicio'
    )
    
    # Service Type
    SERVICE_TYPES = [
        ('individual', 'Individual (1 persona)'),
        ('duo', 'Dúo (2 personas)'),
        ('small_group', 'Grupo pequeño (3-6 personas)'),
        ('large_group', 'Grupo grande (7+ personas)'),
    ]
    
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES,
        default='individual',
        verbose_name='Tipo de sesión'
    )
    
    max_participants = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name='Máximo de participantes',
        help_text='Solo para sesiones grupales'
    )
    
    # Modality
    MODALITIES = [
        ('presencial', 'Presencial'),
        ('online', 'Online'),
        ('a_domicilio', 'A domicilio'),
        ('hibrido', 'Híbrido (Presencial y Online)'),
    ]
    
    modality = models.CharField(
        max_length=20,
        choices=MODALITIES,
        verbose_name='Modalidad'
    )
    
    # Duration
    DURATIONS = [
        (30, '30 minutos'),
        (45, '45 minutos'),
        (60, '60 minutos'),
        (90, '90 minutos'),
        (120, '120 minutos'),
    ]
    
    duration_minutes = models.PositiveIntegerField(
        choices=DURATIONS,
        default=60,
        verbose_name='Duración (minutos)'
    )
    
    # Level
    LEVELS = [
        ('todos', 'Todos los niveles'),
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    
    level = models.CharField(
        max_length=20,
        choices=LEVELS,
        default='todos',
        verbose_name='Nivel'
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Precio',
        help_text='Precio en pesos chilenos (CLP)'
    )
    
    # Additional Info
    what_to_bring = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Qué traer',
        help_text='Ej: Mat de yoga, toalla, botella de agua'
    )
    
    what_includes = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Qué incluye',
        help_text='Ej: Mat proporcionado, espacio climatizado'
    )
    
    # Location (for presencial services)
    location_details = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Detalles de ubicación',
        help_text='Información adicional sobre dónde es la clase'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Visible y disponible para reservas'
    )
    
    # Statistics
    total_bookings = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de reservas'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['professional', 'name']
        indexes = [
            models.Index(fields=['professional', 'is_active']),
            models.Index(fields=['service_type', 'modality']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.professional.user.get_full_name()}"
    
    @property
    def price_formatted(self):
        """Return formatted price."""
        return f"${int(self.price):,}".replace(',', '.')
    
    @property
    def duration_formatted(self):
        """Return formatted duration."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}min"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}min"
    
    def update_statistics(self):
        """Update denormalized statistics."""
        from bookings.models import Booking
        
        self.total_bookings = Booking.objects.filter(
            service=self,
            status__in=['confirmed', 'completed']
        ).count()
        
        self.save(update_fields=['total_bookings'])


class ServiceCategory(models.Model):
    """
    Categories for services (for better organization and filtering).
    Example: Yoga, Pilates, Strength Training, etc.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre'
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug'
    )
    
    description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Descripción'
    )
    
    # Icon/Image (optional)
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Ícono',
        help_text='Nombre del ícono (ej: lucide-icon-name)'
    )
    
    # Ordering
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    
    class Meta:
        verbose_name = 'Categoría de servicio'
        verbose_name_plural = 'Categorías de servicio'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class ServiceTag(models.Model):
    """
    Tags for services (for better filtering and search).
    Example: "Flexibility", "Strength", "Relaxation", "Beginner-friendly"
    """
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nombre'
    )
    
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Slug'
    )
    
    # Many-to-many relationship with services
    services = models.ManyToManyField(
        Service,
        related_name='tags',
        blank=True,
        verbose_name='Servicios'
    )
    
    class Meta:
        verbose_name = 'Etiqueta'
        verbose_name_plural = 'Etiquetas'
        ordering = ['name']
    
    def __str__(self):
        return self.name