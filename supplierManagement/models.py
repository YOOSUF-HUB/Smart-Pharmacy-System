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
    SUPPLIER_TYPE_CHOICES = [
        ("Manufacturer", "Manufacturer"),
        ("Distributor", "Distributor"),
        ("Wholesaler", "Wholesaler"),
        ("Local Vendor", "Local Vendor"),
        ("International Vendor", "International Vendor"),
    ]

    PRODUCT_SUPPLIED_CHOICES = [
        ("Medicines", "Medicines"),
        ("OTC", "OTC"),
        ("Medical Devices", "Medical Devices"),
        ("Non-medical", "Non-medical"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("Blacklisted", "Blacklisted"),
    ]

    supplier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, verbose_name="Supplier Name")
    contact_person = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    supplier_type = models.CharField(max_length=30, choices=SUPPLIER_TYPE_CHOICES, blank=True)
    products_supplied = models.CharField(max_length=30, choices=PRODUCT_SUPPLIED_CHOICES, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True, verbose_name="Tax/Registration Number")
    payment_terms = models.CharField(max_length=50, blank=True, help_text="e.g. Net 30, Net 60, COD")
    bank_details = models.TextField(blank=True, help_text="Optional, for direct payments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    products = models.ManyToManyField(Product, blank=True, related_name="suppliers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
