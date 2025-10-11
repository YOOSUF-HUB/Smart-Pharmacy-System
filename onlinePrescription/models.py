from django.db import models
from django.contrib.auth.models import User

class Prescription(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions')
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
    nic = models.CharField(max_length=20)

    def __str__(self):
        return f"Prescription #{self.id} - {self.user.username}"
