"""
Models for the professionals app.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from pathlib import Path


def professional_photo_path(instance, filename):
    """Generate upload path for professional photos."""
    ext = Path(filename).suffix
    return f'professionals/{instance.user.id}/photo{ext}'


def certification_document_path(instance, filename):
    """Generate upload path for certification documents."""
    ext = Path(filename).suffix
    return f'professionals/{instance.professional.user.id}/certifications/{instance.id}{ext}'


class Professional(models.Model):
    """
    Professional user profile.
    Extends Django User model with professional-specific fields.
    """
    
    # Relationship with Django User
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='professional_profile',
        verbose_name='Usuario'
    )
    
    # Basic Information
    photo = models.ImageField(
        upload_to=professional_photo_path,
        blank=True,
        null=True,
        verbose_name='Foto de perfil',
        help_text='Foto profesional (mínimo 800x800px)'
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Biografía',
        help_text='Descripción breve (máximo 500 caracteres)'
    )
    
    phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
        help_text='Formato: +56912345678'
    )
    
    # Professional Info
    years_of_experience = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        verbose_name='Años de experiencia'
    )
    
    # Specialization
    PRIMARY_SPECIALTIES = [
        ('yoga', 'Yoga'),
        ('pilates', 'Pilates'),
        ('personal_training', 'Entrenamiento Personal'),
        ('functional', 'Entrenamiento Funcional'),
        ('hiit', 'HIIT'),
        ('trx', 'TRX'),
        ('animal_flow', 'Animal Flow'),
        ('calisthenics', 'Calistenia'),
        ('crossfit', 'CrossFit'),
        ('barre', 'Barre'),
        ('zumba', 'Zumba/Baile Fitness'),
        ('running', 'Running Coach'),
        ('cycling', 'Ciclismo'),
        ('other', 'Otro')
    ]
    
    primary_specialty = models.CharField(
        max_length=50,
        choices=PRIMARY_SPECIALTIES,
        verbose_name='Especialidad principal'
    )
    
    # Location
    COMUNAS = [
        ('las_condes', 'Las Condes'),
        ('vitacura', 'Vitacura'),
        ('lo_barnechea', 'Lo Barnechea'),
        ('providencia', 'Providencia'),
        ('nunoa', 'Ñuñoa'),
        ('la_reina', 'La Reina'),
        ('penalolen', 'Peñalolén'),
        ('other', 'Otra')
    ]
    
    comuna = models.CharField(
        max_length=50,
        choices=COMUNAS,
        verbose_name='Comuna base'
    )
    
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Dirección',
        help_text='Dirección del espacio de clases (opcional)'
    )
    
    # Social Media
    instagram_handle = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Instagram',
        help_text='Sin el @, ejemplo: daniela.yoga'
    )
    
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='WhatsApp',
        help_text='Número de contacto WhatsApp'
    )
    
    # Profile Settings
    username_slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Username personalizado',
        help_text='URL personalizada: conecta.cl/tu-username'
    )
    
    # Verification Status
    VERIFICATION_STATUS = [
        ('pending', 'Pendiente de verificación'),
        ('verified', 'Verificado'),
        ('rejected', 'Rechazado'),
    ]
    
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending',
        verbose_name='Estado de verificación'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Perfil visible y puede recibir reservas'
    )
    
    # Statistics (denormalized for performance)
    total_bookings = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de reservas'
    )
    
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name='Rating promedio'
    )
    
    total_reviews = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de reseñas'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de registro'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        verbose_name = 'Profesional'
        verbose_name_plural = 'Profesionales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username_slug']),
            models.Index(fields=['primary_specialty', 'comuna']),
            models.Index(fields=['verification_status', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_primary_specialty_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-generate username_slug if not provided
        if not self.username_slug:
            base_slug = slugify(self.user.get_full_name())
            self.username_slug = base_slug
            
            # Ensure uniqueness
            counter = 1
            while Professional.objects.filter(username_slug=self.username_slug).exists():
                self.username_slug = f"{base_slug}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        """Return professional's full name."""
        return self.user.get_full_name()
    
    @property
    def profile_url(self):
        """Return public profile URL."""
        return f"https://conecta.cl/{self.username_slug}"
    
    @property
    def is_verified(self):
        """Check if professional is verified."""
        return self.verification_status == 'verified'
    
    def update_statistics(self):
        """Update denormalized statistics fields."""
        from bookings.models import Booking
        from reviews.models import Review
        
        # Update total bookings
        self.total_bookings = Booking.objects.filter(
            service__professional=self,
            status='completed'
        ).count()
        
        # Update reviews statistics
        reviews = Review.objects.filter(professional=self)
        self.total_reviews = reviews.count()
        
        if self.total_reviews > 0:
            from django.db.models import Avg
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            self.average_rating = round(avg_rating, 2)
        else:
            self.average_rating = 0.00
        
        self.save(update_fields=['total_bookings', 'total_reviews', 'average_rating'])


class Certification(models.Model):
    """
    Professional certifications/qualifications.
    """
    
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='certifications',
        verbose_name='Profesional'
    )
    
    # Certification Info
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre de la certificación'
    )
    
    institution = models.CharField(
        max_length=200,
        verbose_name='Institución emisora'
    )
    
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
        verbose_name='Año de obtención'
    )
    
    # Document
    document = models.FileField(
        upload_to=certification_document_path,
        verbose_name='Documento',
        help_text='PDF o imagen de la certificación'
    )
    
    # Verification
    VERIFICATION_STATUS = [
        ('pending_review', 'Pendiente de revisión'),
        ('verified', 'Verificada'),
        ('rejected', 'Rechazada'),
    ]
    
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending_review',
        verbose_name='Estado de verificación'
    )
    
    verification_notes = models.TextField(
        blank=True,
        verbose_name='Notas de verificación',
        help_text='Razón de rechazo o comentarios'
    )
    
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_certifications',
        verbose_name='Verificado por'
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de verificación'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de subida'
    )
    
    class Meta:
        verbose_name = 'Certificación'
        verbose_name_plural = 'Certificaciones'
        ordering = ['-year', '-created_at']
        indexes = [
            models.Index(fields=['professional', 'verification_status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.professional.user.get_full_name()}"
    
    @property
    def is_verified(self):
        """Check if certification is verified."""
        return self.verification_status == 'verified'


class AvailabilityBlock(models.Model):
    """
    Recurring availability blocks for professionals.
    Example: "Every Monday 9:00-12:00"
    """
    
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='availability_blocks',
        verbose_name='Profesional'
    )
    
    # Day of week
    DAYS_OF_WEEK = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        verbose_name='Día de la semana'
    )
    
    # Time range
    start_time = models.TimeField(
        verbose_name='Hora de inicio'
    )
    
    end_time = models.TimeField(
        verbose_name='Hora de fin'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    class Meta:
        verbose_name = 'Bloque de disponibilidad'
        verbose_name_plural = 'Bloques de disponibilidad'
        ordering = ['day_of_week', 'start_time']
        indexes = [
            models.Index(fields=['professional', 'day_of_week', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.professional.user.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def clean(self):
        """Validate that end_time is after start_time."""
        from django.core.exceptions import ValidationError
        
        if self.start_time >= self.end_time:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')


class BlockedDate(models.Model):
    """
    Specific dates when professional is not available.
    Example: Vacations, holidays, personal days.
    """
    
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='blocked_dates',
        verbose_name='Profesional'
    )
    
    # Date range
    date = models.DateField(
        verbose_name='Fecha bloqueada'
    )
    
    # Optional: can also block specific time ranges
    all_day = models.BooleanField(
        default=True,
        verbose_name='Todo el día'
    )
    
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de inicio (si no es todo el día)'
    )
    
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de fin (si no es todo el día)'
    )
    
    # Reason (optional)
    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Motivo',
        help_text='Vacaciones, feriado, día personal, etc.'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        verbose_name = 'Fecha bloqueada'
        verbose_name_plural = 'Fechas bloqueadas'
        ordering = ['date']
        indexes = [
            models.Index(fields=['professional', 'date']),
        ]
    
    def __str__(self):
        return f"{self.professional.user.get_full_name()} - {self.date}"
    
    def clean(self):
        """Validate time range if not all day."""
        from django.core.exceptions import ValidationError
        
        if not self.all_day:
            if not self.start_time or not self.end_time:
                raise ValidationError('Debe especificar hora de inicio y fin si no es todo el día.')
            
            if self.start_time >= self.end_time:
                raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')