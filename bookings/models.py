"""
Models for the bookings app.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from clients.models import Client
from services.models import Service
import uuid


class Booking(models.Model):
    """
    Booking/Reservation model.
    Represents a scheduled session between a client and a professional.
    """
    
    # Unique identifier
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='ID de reserva'
    )
    
    # Relationships
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Cliente'
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Servicio'
    )
    
    # Date and Time
    date = models.DateField(
        verbose_name='Fecha de la sesión'
    )
    
    start_time = models.TimeField(
        verbose_name='Hora de inicio'
    )
    
    end_time = models.TimeField(
        verbose_name='Hora de fin'
    )
    
    # Number of participants (for group sessions)
    participants = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Número de participantes'
    )
    
    # Client Information (captured at booking time)
    client_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del cliente',
        help_text='Nombre como aparece en la reserva'
    )
    
    client_email = models.EmailField(
        verbose_name='Email del cliente'
    )
    
    client_phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono del cliente'
    )
    
    # Additional Info
    is_first_time = models.BooleanField(
        default=False,
        verbose_name='Primera vez con el profesional'
    )
    
    client_notes = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Notas del cliente',
        help_text='Comentarios especiales, lesiones, objetivos, etc.'
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending_payment', 'Pendiente de pago'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Completada'),
        ('cancelled_by_client', 'Cancelada por cliente'),
        ('cancelled_by_professional', 'Cancelada por profesional'),
        ('no_show', 'Cliente no asistió'),
    ]
    
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending_payment',
        verbose_name='Estado'
    )
    
    # Cancellation
    cancellation_reason = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Razón de cancelación'
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de cancelación'
    )
    
    # Pricing (captured at booking time, may differ from current service price)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Precio',
        help_text='Precio al momento de la reserva'
    )
    
    # Commission (for future monetization)
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name='Porcentaje de comisión',
        help_text='Comisión de la plataforma (%)'
    )
    
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name='Monto de comisión'
    )
    
    # Payment
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('completed', 'Completado'),
            ('failed', 'Fallido'),
            ('refunded', 'Reembolsado'),
        ],
        default='pending',
        verbose_name='Estado del pago'
    )
    
    # Reminders
    reminder_sent_24h = models.BooleanField(
        default=False,
        verbose_name='Recordatorio 24hrs enviado'
    )
    
    reminder_sent_2h = models.BooleanField(
        default=False,
        verbose_name='Recordatorio 2hrs enviado'
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
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de completado'
    )
    
    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['client', 'date']),
            models.Index(fields=['service', 'date']),
            models.Index(fields=['status', 'date']),
            models.Index(fields=['date', 'start_time']),
        ]
        unique_together = ['service', 'date', 'start_time']
    
    def __str__(self):
        return f"Reserva #{self.booking_id} - {self.client_name} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Calculate commission
        if self.commission_percentage > 0:
            self.commission_amount = (self.price * self.commission_percentage) / 100
        
        # Set end_time based on service duration
        if not self.end_time and self.start_time:
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(self.date, self.start_time)
            end_datetime = start_datetime + timedelta(minutes=self.service.duration_minutes)
            self.end_time = end_datetime.time()
        
        super().save(*args, **kwargs)
    
    @property
    def professional(self):
        """Get the professional from the service."""
        return self.service.professional
    
    @property
    def is_past(self):
        """Check if booking is in the past."""
        from datetime import datetime
        booking_datetime = datetime.combine(self.date, self.start_time)
        return booking_datetime < timezone.now()
    
    @property
    def is_upcoming(self):
        """Check if booking is upcoming."""
        return not self.is_past and self.status == 'confirmed'
    
    @property
    def can_be_cancelled(self):
        """Check if booking can be cancelled."""
        if self.status not in ['confirmed', 'pending_payment']:
            return False
        
        # Can't cancel if already past
        if self.is_past:
            return False
        
        # Can't cancel if less than 24hrs before (configurable)
        from datetime import datetime, timedelta
        booking_datetime = datetime.combine(self.date, self.start_time)
        min_cancellation_time = booking_datetime - timedelta(hours=24)
        
        return timezone.now() < min_cancellation_time
    
    def cancel(self, reason='', by_professional=False):
        """Cancel the booking."""
        if not self.can_be_cancelled and not by_professional:
            raise ValueError('Esta reserva no puede ser cancelada')
        
        if by_professional:
            self.status = 'cancelled_by_professional'
        else:
            self.status = 'cancelled_by_client'
        
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.save()
        
        # TODO: Send cancellation notification
        # TODO: Process refund if applicable
    
    def mark_as_completed(self):
        """Mark booking as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update statistics
        self.client.update_statistics()
        self.service.update_statistics()
        self.service.professional.update_statistics()
    
    def mark_as_no_show(self):
        """Mark booking as no-show."""
        self.status = 'no_show'
        self.save()


class BookingNote(models.Model):
    """
    Notes added by professional about a booking/client.
    Private notes for professional use only.
    """
    
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Reserva'
    )
    
    note = models.TextField(
        max_length=1000,
        verbose_name='Nota'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        verbose_name = 'Nota de reserva'
        verbose_name_plural = 'Notas de reservas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Nota para {self.booking}"
