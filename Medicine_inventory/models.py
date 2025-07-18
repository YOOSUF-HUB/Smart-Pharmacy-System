from django.db import models
from datetime import date

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    category = models.CharField(max_length=50)  # e.g., Tablet, Syrup, Injection
    description = models.TextField(blank=True)
    dosage = models.CharField(max_length=50)  # e.g., 500mg
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_in_stock = models.PositiveIntegerField()
    reorder_level = models.PositiveIntegerField(default=10)  # Minimum quantity before restock alert
    manufacture_date = models.DateField()
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=50, unique=True)
    supplier = models.CharField(max_length=100)  # You can replace this with a ForeignKey to Supplier model

    def is_expired(self):
        return date.today() > self.expiry_date

    def __str__(self):
        return f"{self.name} - {self.dosage} ({self.batch_number})"