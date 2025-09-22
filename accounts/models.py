# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds role-based authentication and additional fields for staff management.
    Fields already in AbstractUser: id, first_name, last_name, email, password, is_active
    """
    # Define user role choices for the pharmacy system
    ROLE_CHOICES = (
        ('customer', 'Customer'),      # Regular customers who buy products
        ('admin', 'Admin'),            # System administrators with full access
        ('pharmacist', 'Pharmacist'),  # Staff who manage medicine inventory
        ('cashier', 'Cashier'),        # Staff who handle sales transactions
    )
    
    # Role field to determine user permissions and dashboard access
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    
    # Contact information for all users
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Date hired field primarily for staff members (admin, pharmacist, cashier)
    date_hired = models.DateField(default=timezone.now, null=True, blank=True)

    def __str__(self):
        # Display username and role for easy identification in admin panel
        return f"{self.username} ({self.role})"


class Customer(models.Model):
    """
    Customer profile model with additional information.
    Extends the User model with customer-specific fields for detailed profiles.
    One-to-one relationship with User model for customers only.
    """
    # Link to User model - deletes customer profile if user is deleted
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Contact information (separate from User.phone for additional flexibility)
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Address information for delivery and billing purposes
    address = models.TextField(blank=True, null=True)
    
    # Additional location details for shipping/delivery
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # National Identity Card number for verification purposes
    nic = models.CharField(max_length=20, blank=True, null=True, verbose_name="NIC Number")
    
    def __str__(self):
        # Return username for easy identification
        return self.user.username
    
    # Property methods to access User fields directly from Customer instance
    # This allows easier access to user data without always going through customer.user
    
    @property
    def id(self):
        """Get the user ID directly from customer instance"""
        return self.user.id
    
    @property
    def first_name(self):
        """Get the first name directly from customer instance"""
        return self.user.first_name
    
    @property
    def last_name(self):
        """Get the last name directly from customer instance"""
        return self.user.last_name
    
    @property
    def email(self):
        """Get the email directly from customer instance"""
        return self.user.email
    
    @property
    def date_joined(self):
        """Get the registration date directly from customer instance"""
        return self.user.date_joined