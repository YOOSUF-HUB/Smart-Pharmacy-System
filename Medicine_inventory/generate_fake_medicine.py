import os
import sys
import django
import random
from faker import Faker
from datetime import date


project_root = "/Users/yoosufahamed/Desktop/Projects/Y2S2_Project/Y2S2_Project_SLIIT"
sys.path.insert(0, project_root) #locate python crudDemo as package

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crudDemo.settings")
django.setup()

from Medicine_inventory.models import Medicine

fake = Faker()
# List of real medicine names, brands, and categories for generating fake data

real_medicine_names = [
    "Paracetamol", "Ibuprofen", "Amoxicillin", "Metformin", "Aspirin",
    "Omeprazole", "Atorvastatin", "Cetirizine", "Azithromycin", "Simvastatin",
    "Lisinopril", "Levothyroxine", "Hydrochlorothiazide", "Metoprolol", "Losartan",
    "Clopidogrel", "Gabapentin", "Prednisone", "Alprazolam", "Zolpidem"
]

real_brands = [
    "Pfizer", "GlaxoSmithKline", "Novartis", "Roche", "Sanofi",
    "Johnson & Johnson", "Merck", "AbbVie", "AstraZeneca", "Bayer",
    "Eli Lilly", "Takeda", "Bristol-Myers Squibb", "Teva", "Amgen"
]

categories = [
    "Analgesic",              # Pain relief
    "Antibiotic",             # Bacterial infections
    "Antipyretic",            # Fever reducers
    "Antihistamine",          # Allergy relief
    "Antacid",                # Acid reflux, ulcers
    "Antidepressant",         # Mood disorders
    "Antihypertensive",       # Blood pressure control
    "Antidiabetic",           # Blood sugar control
    "Antiviral",              # Viral infections
    "Steroid",                # Corticosteroids / inflammation
    "Diuretic",               # Fluid removal
    "Sedative",               # Sleep aid / anxiety
    "Vaccine",                # Immunization
    "Antifungal",             # Fungal infections
    "Bronchodilator",         # Asthma / COPD
    "Anticoagulant",          # Blood thinners
    "Contraceptive",          # Birth control
    "Antiemetic",             # Nausea / vomiting
    "Antipsychotic",          # Mental health
    "Muscle Relaxant",        # Muscle spasms
    "Chemotherapy",           # Cancer treatment
    "Immunosuppressant",      # Autoimmune / transplants
    "Ophthalmic",             # Eye conditions
    "Dermatological",         # Skin treatments
    "Nutritional Supplement", # Vitamins / minerals
    "Respiratory Agent",      # Cold, cough, asthma
    "Local Anesthetic"        # Numbing agents
]

dosages = [
    "100mg", "250mg", "500mg", "5mg", "10mg", "20mg", "50mg", "1g", "2g", "10ml", "15ml"
]

suppliers = [
    "McKesson Corporation", "Cardinal Health", "AmerisourceBergen",
    "Medline Industries", "Henry Schein", "Cipla Distributors", "Sun Pharma Supply Co."
]

def generate_batch_number(med_name, supplier, seq):
    med_code = med_name[:3].upper()
    today_str = date.today().strftime("%Y%m%d")
    supplier_code = supplier.split()[0].upper()
    return f"{med_code}-{today_str}-{supplier_code}-{seq:03d}"

def create_fake_medicine(n=10):
    for i in range(n):
        med_name = random.choice(real_medicine_names)
        supplier = random.choice(suppliers)
        batch_number = generate_batch_number(med_name, supplier, i+1)
        Medicine.objects.create(
            name=med_name,
            brand=random.choice(real_brands),
            category=random.choice(categories),
            description=fake.text(max_nb_chars=100),
            dosage=random.choice(dosages),
            price=round(random.uniform(10, 500), 2),
            quantity_in_stock=random.randint(1, 100),
            reorder_level=random.randint(5, 20),
            manufacture_date=fake.date_between(start_date='-2y', end_date='today'),
            expiry_date=fake.date_between(start_date='today', end_date='+2y'),
            batch_number=batch_number,
            supplier=supplier,
        )
    print(f"{n} fake medicines created.")

if __name__ == "__main__":
    create_fake_medicine(50)