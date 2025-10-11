from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings

NIC_REGEX = r'^(?:\d{9}[VvXx]|\d{12})$'
nic_validator = RegexValidator(
    NIC_REGEX,
    message="Enter a valid Sri Lankan NIC (old: 9 digits + V/v/X, or new: 12 digits)."
)
class Prescription(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Approved', 'Approved'),
        ('Available for Pickup', 'Available for Pickup'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    prescription_image = models.ImageField(upload_to='prescriptions/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    pharmacist_comment = models.TextField(blank=True, null=True)
    order = models.OneToOneField(
        'onlineStore.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescription'
    )
    nic = models.CharField(max_length=12, validators=[nic_validator], unique=True, help_text="Enter 9-digit + V/v/X (old) or 12-digit (new) NIC")

    def __str__(self):
        return f"Prescription #{self.id} - {self.user.username}"
