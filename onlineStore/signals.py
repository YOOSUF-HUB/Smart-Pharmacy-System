# onlineStore/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from Medicine_inventory.models import Medicine
from .models import Products

@receiver(post_save, sender=Medicine)
def create_product_for_medicine(sender, instance, created, **kwargs):
    if created:
        # Create a Products entry for the newly added medicine
        Products.objects.create(
            product_type='Medicine',
            medicine=instance,
            featured=False,
            available_online=True
        )
