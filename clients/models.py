"""
Models for the clients app.
"""

from django.db import models
from django.contrib.auth.models import User
from professionals.models import Professional


class Client(models.Model):
    """
    Client user profile.
    Extends Django User model with client-specific fields.
    """
    
    # Relationship with Django User
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name='Usuario'
    )
    
    # Contact Info
    phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
        help_text='Formato: +56912345678'
    )
    
    # Preferences
    EXPERIENCE_LEVELS = [
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
    ]
    
    fitness_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVELS,
        blank=True,
        verbose_name='Nivel de experiencia'
    )
    
    # Notes (for professionals to see)
    notes = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name='Notas',
        help_text='Información adicional, lesiones, objetivos, etc.'
    )
    
    # Statistics
    total_bookings = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de reservas'
    )
    
    total_completed_bookings = models.PositiveIntegerField(
        default=0,
        verbose_name='Reservas completadas'
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
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()}"
    
    @property
    def full_name(self):
        """Return client's full name."""
        return self.user.get_full_name()
    
    def update_statistics(self):
        """Update denormalized statistics fields."""
        from bookings.models import Booking
        
        # Update total bookings
        self.total_bookings = Booking.objects.filter(client=self).count()
        
        # Update completed bookings
        self.total_completed_bookings = Booking.objects.filter(
            client=self,
            status='completed'
        ).count()
        
        self.save(update_fields=['total_bookings', 'total_completed_bookings'])


class Favorite(models.Model):
    """
    Client's favorite professionals.
    """
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Cliente'
    )
    
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Profesional'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de agregado'
    )
    
    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        ordering = ['-created_at']
        unique_together = ['client', 'professional']
        indexes = [
            models.Index(fields=['client', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.client.user.get_full_name()} ♥ {self.professional.user.get_full_name()}"