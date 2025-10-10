import os
import django
from faker import Faker
import random

# --- 1. Setup Django Environment ---
# IMPORTANT: You must replace 'YOUR_PROJECT_NAME' below with the actual 
# name of the directory that contains your settings.py file.
# Example: If settings.py is in 'smart_pharmacy', use 'smart_pharmacy.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Pharmarcy_Prescription_Tracker.settings')
django.setup()

# --- 2. Import your Doctor Model ---
# The Doctor model is in the 'prescriptions' app's models.py
from prescriptions.models import Doctor 

# --- 3. Initialize Faker and Specializations ---
# Using Indian locale for realistic names and contact structure
fake = Faker('en_IN') 

# Common specializations for pharmacy/medical systems
SPECIALIZATIONS = [
    "General Practitioner", "Dermatologist", "Pediatrician", 
    "Cardiologist", "Orthopedic Surgeon", "Neurologist", 
    "Ophthalmologist", "ENT Specialist", "Gastroenterologist", 
    "Endocrinologist", "Urologist", "Psychiatrist"
]

def create_fake_doctors(n=500):
    """Generates and saves N fake Doctor records based on the provided model structure."""
    print(f"Starting creation of {n} fake doctor records...")
    doctors_to_create = []
    
    # Pre-fetch existing medical codes for uniqueness check
    existing_codes = set(Doctor.objects.values_list('medical_code', flat=True))

    for _ in range(n):
        
        # Generate a unique medical code in a Sri Lankan format (SLMC)
        # Format: SLMC/Reg/ + 5 random digits (e.g., SLMC/Reg/12345)
        while True:
            # FIX: Use random_int and str formatting to ensure 5 digits with leading zeros
            code_int = fake.unique.random_int(min=1, max=99999)
            code_suffix = f"{code_int:05d}" # Formats the integer with 5 digits, padding with zeros
            medical_code = f"SLMC/Reg/{code_suffix}" 
            
            if medical_code not in existing_codes:
                existing_codes.add(medical_code)
                break
        
        # Clean the phone number format to ensure it fits CharField max_length=20
        # Generates a 10-digit number like 771234567, common in SL
        contact_num = fake.numerify('##########') 
        
        doctor = Doctor(
            # Names generated from en_IN locale (many shared names with SL)
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            specialization=random.choice(SPECIALIZATIONS),
            contact_number=contact_num,
            medical_code=medical_code,
        )
        doctors_to_create.append(doctor)
    
    # Bulk creation is the most efficient way to insert many records
    Doctor.objects.bulk_create(doctors_to_create)
    print(f"Successfully created {n} fake doctors.")

if __name__ == '__main__':
    # Updated to 500 as per your last attempt
    create_fake_doctors(n=500)
