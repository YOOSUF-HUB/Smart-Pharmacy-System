from django.db import models

from Pharmarcy_Prescription_Tracker import settings

# Create your models here.
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120)
    line1 = models.CharField(max_length=120)
    line2 = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=80)
    province = models.CharField(max_length=80)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default="Sri Lanka")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)