"""
Models for the reviews app.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from clients.models import Client
from professionals.models import Professional
from bookings.models import Booking


class Review(models.Model):
    """
    Review/Rating left by a client for a professional after a completed booking.
    """
    
    # Relationships
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Cliente'
    )
    
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Profesional'
    )
    
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Reserva',
        help_text='Reserva asociada a esta reseña'
    )
    
    # Rating (1-5 stars)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Calificación',
        help_text='Estrellas de 1 a 5'
    )
    
    # Review Text (optional)
    comment = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name='Comentario',
        help_text='Comentario sobre la experiencia (opcional)'
    )
    
    # Professional Response
    professional_response = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Respuesta del profesional'
    )
    
    professional_response_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de respuesta'
    )
    
    # Moderation
    is_approved = models.BooleanField(
        default=True,
        verbose_name='Aprobada',
        help_text='Reseña visible públicamente'
    )
    
    is_flagged = models.BooleanField(
        default=False,
        verbose_name='Marcada',
        help_text='Marcada para revisión por contenido inapropiado'
    )
    
    flagged_reason = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Razón de marcado'
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
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['professional', 'is_approved']),
            models.Index(fields=['rating', 'is_approved']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        stars = '⭐' * self.rating
        return f"{stars} - {self.client.user.get_full_name()} → {self.professional.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update professional's rating statistics
        if is_new:
            self.professional.update_statistics()
    
    @property
    def client_display_name(self):
        """Return client's first name only for privacy."""
        return self.client.user.first_name or 'Cliente'
    
    @property
    def rating_display(self):
        """Return rating as stars."""
        return '⭐' * self.rating
    
    def add_professional_response(self, response_text):
        """Add professional's response to the review."""
        from django.utils import timezone
        
        self.professional_response = response_text
        self.professional_response_date = timezone.now()
        self.save()
    
    def flag(self, reason=''):
        """Flag review for moderation."""
        self.is_flagged = True
        self.flagged_reason = reason
        self.is_approved = False  # Hide while under review
        self.save()
    
    def approve(self):
        """Approve flagged review."""
        self.is_flagged = False
        self.is_approved = True
        self.flagged_reason = ''
        self.save()


class ReviewReport(models.Model):
    """
    Report of inappropriate review by users.
    """
    
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Reseña'
    )
    
    # Reporter (optional, can be anonymous)
    reported_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_reports',
        verbose_name='Reportado por'
    )
    
    # Reason
    REPORT_REASONS = [
        ('inappropriate', 'Contenido inapropiado'),
        ('offensive', 'Lenguaje ofensivo'),
        ('spam', 'Spam'),
        ('fake', 'Reseña falsa'),
        ('harassment', 'Acoso'),
        ('other', 'Otro'),
    ]
    
    reason = models.CharField(
        max_length=20,
        choices=REPORT_REASONS,
        verbose_name='Razón'
    )
    
    details = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Detalles'
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('reviewed', 'Revisado'),
        ('action_taken', 'Acción tomada'),
        ('dismissed', 'Desestimado'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    
    resolution_notes = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Notas de resolución'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de reporte'
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de resolución'
    )
    
    class Meta:
        verbose_name = 'Reporte de reseña'
        verbose_name_plural = 'Reportes de reseñas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Reporte: {self.review} - {self.get_reason_display()}"