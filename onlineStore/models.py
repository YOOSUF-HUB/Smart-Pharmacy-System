from django.conf import settings
from django.db import models
from Medicine_inventory.models import Medicine
from Non_Medicine_inventory.models import NonMedicalProduct



# Create your models here.

class Products(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('Medicine', 'Medicine'),
        ('NonMedicalProduct', 'NonMedicalProduct'),
    ]

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    medicine = models.ForeignKey(
        Medicine, on_delete=models.CASCADE, null=True, blank=True
    )
    non_medical_product = models.ForeignKey(
        NonMedicalProduct, on_delete=models.CASCADE, null=True, blank=True
    )

    featured = models.BooleanField(default=False)
    available_online = models.BooleanField(default=True)

    def __str__(self):
        if self.product_type == 'Medicine' and self.medicine:
            return f"{self.medicine.name} ({self.medicine.dosage})"
        elif self.product_type == 'NonMedicalProduct' and self.non_medical_product:
            return f"{self.non_medical_product.name}"
        return "Unknown Product"
    

    
# class Cart(models.Model):
#     cart_id = models.AutoField(primary_key=True)
#     customer_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
#     product = models.ForeignKey('Products', on_delete=models.CASCADE) 
#     quantity = models.PositiveIntegerField(default=1)
#     created_at = models.DateTimeField(auto_now_add=True)


#     def __str__(self):
#         return f"Cart({self.user}, {self.product}, {self.quantity})"


# class CartItem(models.Model):
#     cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
#     product = models.ForeignKey('Products', on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField(default=1)

#     def __str__(self):
#         return f"CartItem({self.cart}, {self.product}, {self.quantity})"

# class Order(models.Model):
#     ORDER_STATUS = [
#         ('Pending', 'Pending'),
#         ('Shipped', 'Shipped'),
#         ('Delivered', 'Delivered'),
#         ('Cancelled', 'Cancelled'),
#     ]

#     order_id = models.AutoField(primary_key=True)
#     customer_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Pending')
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"Order({self.user}, {self.cart}, {self.created_at})"
    

# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE)
#     product = models.ForeignKey('Products', on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField(default=1)
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"OrderItem({self.order}, {self.product}, {self.quantity})"
