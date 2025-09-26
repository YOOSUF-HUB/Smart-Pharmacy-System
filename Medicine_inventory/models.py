from django.db import models
from datetime import date, timedelta
from django.conf import settings


class Medicine(models.Model):
    CATEGORY_CHOICES = [
    ('Analgesic', 'Analgesic'),               # Pain relief
    ('Antibiotic', 'Antibiotic'),             # Bacterial infections
    ('Antiviral', 'Antiviral'),               # Viral infections
    ('Antifungal', 'Antifungal'),             # Fungal infections
    ('Antihistamine', 'Antihistamine'),       # Allergy relief
    ('Antacid', 'Antacid'),                   # Acid reflux, ulcers
    ('Antipyretic', 'Antipyretic'),           # Fever reducers
    ('Anti-inflammatory', 'Anti-inflammatory'),# Inflammation reduction
    ('Antihypertensive', 'Antihypertensive'), # Blood pressure
    ('Antidiabetic', 'Antidiabetic'),         # Blood sugar control
    ('Antidepressant', 'Antidepressant'),     # Mood disorders
    ('Anticoagulant', 'Anticoagulant'),       # Blood thinners
    ('Diuretic', 'Diuretic'),                 # Fluid removal
    ('Sedative', 'Sedative'),                 # Anxiety, sleep aid
    ('Bronchodilator', 'Bronchodilator'),     # Asthma/COPD
    ('Vaccine', 'Vaccine'),                   # Immunization
    ('Steroid', 'Steroid'),                   # Corticosteroids
    ('Contraceptive', 'Contraceptive'),       # Birth control
    ('Antiemetic', 'Antiemetic'),             # Nausea/vomiting
    ('Antipsychotic', 'Antipsychotic'),       # Mental illness
    ('Muscle Relaxant', 'Muscle Relaxant'),   # Muscle spasms
    ('Chemotherapy', 'Chemotherapy'),         # Cancer treatment
    ('Immunosuppressant', 'Immunosuppressant'),# Transplant, autoimmune
    ('Ophthalmic', 'Ophthalmic'),             # Eye treatments
    ('Dermatological', 'Dermatological'),     # Skin applications
    ('Nutritional Supplement', 'Nutritional Supplement'), # Vitamins
    ('Respiratory Agent', 'Respiratory Agent'),# Cough, congestion
    ('Local Anesthetic', 'Local Anesthetic'), # Numbing agents
    ]

    MEDICINE_TYPE_CHOICES = [
        ('RX', 'RX'),
        ('OTC', 'OTC'),
    ]

    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    medicine_type = models.CharField(max_length=10,choices=MEDICINE_TYPE_CHOICES,default='RX')
    description = models.TextField(blank=True)
    dosage = models.CharField(max_length=50)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='medical_products/', blank=True, null=True)
    quantity_in_stock = models.PositiveIntegerField()
    reorder_level = models.PositiveIntegerField(default=10)
    manufacture_date = models.DateField()
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=150, unique=True)  # This should already be unique
    available_online = models.BooleanField(default=False, help_text="Make this medicine available for online purchase")
    
    # supplier = models.CharField(max_length=100)
    supplier = models.ForeignKey(
        'supplierManagement.Supplier',  # Use string reference
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicines'
    )

    def is_expired(self):
        return date.today() >= self.expiry_date

    def is_near_expiry(self):
        return (
            self.expiry_date
            and date.today() < self.expiry_date
            and (self.expiry_date - date.today()) <= timedelta(days=7)
        )

    def __str__(self):
        return f"{self.name} - {self.dosage} ({self.batch_number})"

    def clean(self):
        from django.core.exceptions import ValidationError
        from datetime import date
        
        # Prevent future manufacture dates
        if self.manufacture_date and self.manufacture_date > date.today():
            raise ValidationError({
                'manufacture_date': 'Manufacture date cannot be in the future.'
            })
            
        # Ensure expiry date is after manufacture date
        if self.manufacture_date and self.expiry_date:
            if self.expiry_date <= self.manufacture_date:
                raise ValidationError({
                    'expiry_date': 'Expiry date must be after manufacture date.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()  # This will call clean() method
        super().save(*args, **kwargs)

    @property
    def total_value(self):
        """Calculate total value of stock for this medicine"""
        if self.price and self.quantity_in_stock:
            return self.price * self.quantity_in_stock
        return 0

    def can_be_deleted(self):
        """
        Check if this medicine can be safely deleted.
        Returns False if it's referenced by other models.
        """
        try:
            # Check if medicine is used in prescriptions
            if hasattr(self, 'prescriptionitem_set') and self.prescriptionitem_set.exists():
                return False
            
            # Check if medicine is used in payments/sales
            if hasattr(self, 'paymentitem_set') and self.paymentitem_set.exists():
                return False
            
            # Add other related model checks as needed
            return True
        except:
            return False
    
    
class MedicineAction(models.Model):
    ACTION_CHOICES = [
        ('Created', 'Created'),
        ('Updated', 'Updated'),
        ('Deleted', 'Deleted'),
    ]
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, blank=True)
    medicine_name = models.CharField(max_length=255, blank=True, null=True)
    batch_number = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.medicine.name} {self.get_action_display()} at {self.timestamp}"