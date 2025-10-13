from django.db import models
from django.core.validators import MinValueValidator


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Tablet", "Tablet"),
        ("Capsule", "Capsule"),
        ("Syrup", "Syrup"),
        ("Injection", "Injection"),
    ]
    name = models.CharField(max_length=120, unique=True, default="Medicines")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.name


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
    STATUS_CHOICES = [("Active","Active"),("Inactive","Inactive"),("Blacklisted","Blacklisted")]

    supplier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, verbose_name="Supplier Name")
    contact_person = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    supplier_type = models.CharField(max_length=50, choices=SUPPLIER_TYPE_CHOICES, blank=True)
    products_supplied = models.CharField(max_length=50, choices=PRODUCT_SUPPLIED_CHOICES, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    payment_terms = models.CharField(max_length=200, blank=True)
    bank_details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    products = models.ManyToManyField(Product, related_name="suppliers", blank=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("Pending","Pending"),
        ("Ordered","Ordered"),
        ("Delivered","Delivered"),
        ("Cancelled","Cancelled"),
    ]
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    order_date = models.DateField(auto_now_add=True, editable=False)
    expected_delivery = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"PO #{self.pk} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    # Optional link to Product if it exists; free-typed name is always stored
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True, related_name="purchase_items")
    product_name = models.CharField(max_length=150, default="Unknown Product")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    def get_subtotal(self):
        return self.quantity * self.price