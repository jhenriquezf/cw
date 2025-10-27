"""
Models for the payments app.
"""

from django.db import models
from django.core.validators import MinValueValidator
from bookings.models import Booking
from professionals.models import Professional
import uuid


class Payment(models.Model):
    """
    Payment transaction model.
    Handles payments through Flow, Mercado Pago, or other gateways.
    """
    
    # Unique identifier
    payment_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='ID de pago'
    )
    
    # Relationship
    booking = models.OneToOneField(
        Booking,
        on_delete=models.PROTECT,
        related_name='payment',
        verbose_name='Reserva'
    )
    
    # Payment Gateway
    PAYMENT_GATEWAYS = [
        ('flow', 'Flow'),
        ('mercadopago', 'Mercado Pago'),
        ('stripe', 'Stripe'),
        ('manual', 'Manual/Transferencia'),
    ]
    
    gateway = models.CharField(
        max_length=20,
        choices=PAYMENT_GATEWAYS,
        default='flow',
        verbose_name='Pasarela de pago'
    )
    
    # Gateway Transaction ID
    gateway_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='ID de transacción en pasarela',
        help_text='ID de la transacción en Flow/MercadoPago'
    )
    
    # Amounts
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Monto total',
        help_text='Monto en CLP'
    )
    
    currency = models.CharField(
        max_length=3,
        default='CLP',
        verbose_name='Moneda'
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    
    # Payment Method (captured from gateway)
    PAYMENT_METHODS = [
        ('credit_card', 'Tarjeta de crédito'),
        ('debit_card', 'Tarjeta de débito'),
        ('bank_transfer', 'Transferencia bancaria'),
        ('other', 'Otro'),
    ]
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        blank=True,
        verbose_name='Método de pago'
    )
    
    # Gateway Response
    gateway_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Respuesta de la pasarela',
        help_text='Response completo del gateway en JSON'
    )
    
    # Error handling
    error_message = models.TextField(
        blank=True,
        verbose_name='Mensaje de error',
        help_text='Descripción del error si el pago falló'
    )
    
    # Refund
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name='Monto reembolsado'
    )
    
    refund_reason = models.TextField(
        blank=True,
        verbose_name='Razón del reembolso'
    )
    
    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de reembolso'
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
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['status', 'gateway']),
            models.Index(fields=['gateway_transaction_id']),
        ]
    
    def __str__(self):
        return f"Pago #{self.payment_id} - {self.get_status_display()}"
    
    @property
    def is_successful(self):
        """Check if payment was successful."""
        return self.status == 'completed'
    
    @property
    def can_be_refunded(self):
        """Check if payment can be refunded."""
        return self.status == 'completed' and self.refund_amount < self.amount
    
    def mark_as_completed(self):
        """Mark payment as completed."""
        from django.utils import timezone
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update booking status
        self.booking.status = 'confirmed'
        self.booking.payment_status = 'completed'
        self.booking.save()
    
    def mark_as_failed(self, error_message=''):
        """Mark payment as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
        
        # Update booking status
        self.booking.payment_status = 'failed'
        self.booking.save()
    
    def process_refund(self, amount=None, reason=''):
        """Process a refund for this payment."""
        from django.utils import timezone
        
        if not self.can_be_refunded:
            raise ValueError('Este pago no puede ser reembolsado')
        
        refund_amount = amount or (self.amount - self.refund_amount)
        
        if refund_amount > (self.amount - self.refund_amount):
            raise ValueError('El monto de reembolso excede el monto disponible')
        
        # Update refund fields
        self.refund_amount += refund_amount
        self.refund_reason = reason
        self.refunded_at = timezone.now()
        
        # Update status
        if self.refund_amount >= self.amount:
            self.status = 'refunded'
            self.booking.payment_status = 'refunded'
        
        self.save()
        self.booking.save()
        
        # TODO: Call gateway API to process actual refund
        
        return refund_amount


class Payout(models.Model):
    """
    Payout to professionals.
    When platform commission is applied, this tracks money transfers to professionals.
    """
    
    # Unique identifier
    payout_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='ID de pago'
    )
    
    # Relationship
    professional = models.ForeignKey(
        Professional,
        on_delete=models.PROTECT,
        related_name='payouts',
        verbose_name='Profesional'
    )
    
    # Amount
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Monto'
    )
    
    # Related bookings (many-to-many through intermediate model)
    # This payout covers these bookings
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    
    # Bank Details (captured at payout time)
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Banco'
    )
    
    account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de cuenta'
    )
    
    account_holder = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Titular de la cuenta'
    )
    
    # Transaction reference
    transaction_reference = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Referencia de transacción'
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de completado'
    )
    
    class Meta:
        verbose_name = 'Pago a profesional'
        verbose_name_plural = 'Pagos a profesionales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['professional', 'status']),
        ]
    
    def __str__(self):
        return f"Payout #{self.payout_id} - {self.professional.user.get_full_name()}"


class PayoutBooking(models.Model):
    """
    Intermediate model linking payouts to bookings.
    Tracks which bookings are included in each payout.
    """
    
    payout = models.ForeignKey(
        Payout,
        on_delete=models.CASCADE,
        related_name='payout_bookings',
        verbose_name='Pago'
    )
    
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payout_bookings',
        verbose_name='Reserva'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Monto',
        help_text='Monto que corresponde a esta reserva'
    )
    
    class Meta:
        verbose_name = 'Reserva en pago'
        verbose_name_plural = 'Reservas en pagos'
        unique_together = ['payout', 'booking']
    
    def __str__(self):
        return f"{self.payout} - {self.booking}"
