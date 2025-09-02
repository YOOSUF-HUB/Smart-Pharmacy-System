from django.db import models
from Medicine_inventory.models import Medicine

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(
        max_length=50,
        choices=Medicine.CATEGORY_CHOICES
    )

    def __str__(self):
        return f"{self.name} ({self.category})"


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(Product, blank=True, related_name="suppliers")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
