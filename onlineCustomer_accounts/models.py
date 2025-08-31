from django.db import models
from accounts.models import User

# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_customer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=240, blank=True, null=True)
    city = models.CharField(max_length=80, blank=True, null=True)
    province = models.CharField(max_length=80, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=2, default="Sri Lanka")
    created_at = models.DateTimeField(auto_now_add=True)