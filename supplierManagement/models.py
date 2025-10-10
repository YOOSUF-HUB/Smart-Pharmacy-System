from django.db import models


# Create your models here.
class Product(models.Model):

    CATEGORY_CHOICES = [
    ("Tablet", "Tablet"),
    ("Capsule", "Capsule"),
    ("Syrup", "Syrup"),
    ("Injection", "Injection"),
    ]

    name = models.CharField(max_length=120)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        null=True
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


class PurchaseOrder(models.Model):
    STATUS_PENDING = "Pending"
    STATUS_SHIPPED = "Shipped"
    STATUS_DELIVERED = "Delivered"
    STATUS_DELAYED = "Delayed"
    STATUS_CANCELLED = "Cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_DELAYED, "Delayed"),
        (STATUS_CANCELLED , "Cancelled")
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_orders")
    order_date = models.DateField(auto_now_add=True)
    expected_delivery = models.DateField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PO-{self.id} | {self.supplier.name}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"