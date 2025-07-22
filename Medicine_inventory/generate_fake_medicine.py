import os
import django
import random
from faker import Faker

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crudDemo.settings')
django.setup()

from Medicine_inventory.models import Medicine

fake = Faker()

categories = ['Tablet', 'Syrup', 'Injection', 'Capsule', 'Ointment']


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
    "Analgesic", "Antibiotic", "Antipyretic", "Antihistamine", "Antacid",
    "Antidepressant", "Antihypertensive", "Antidiabetic", "Antiviral", "Steroid",
    "Diuretic", "Sedative", "Vaccine", "Antifungal", "Bronchodilator"
]

dosages = [
    "100mg", "250mg", "500mg", "5mg", "10mg", "20mg", "50mg", "1g", "2g", "10ml", "15ml"
]

suppliers = [
    "McKesson Corporation", "Cardinal Health", "AmerisourceBergen",
    "Medline Industries", "Henry Schein", "Cipla Distributors", "Sun Pharma Supply Co."
]

def create_fake_medicine(n=10):
    for _ in range(n):
        Medicine.objects.create(
            name=random.choice(real_medicine_names),
            brand=random.choice(real_brands),
            category=random.choice(categories),
            description=fake.text(max_nb_chars=100),
            dosage=random.choice(dosages),
            price=round(random.uniform(10, 500), 2),
            quantity_in_stock=random.randint(1, 100),
            reorder_level=random.randint(5, 20),
            manufacture_date=fake.date_between(start_date='-2y', end_date='today'),
            expiry_date=fake.date_between(start_date='today', end_date='+2y'),
            batch_number=fake.unique.bothify(text='RX-###-##'),
            supplier=random.choice(suppliers)
        )
    print(f"{n} fake medicines created.")

if __name__ == "__main__":
    create_fake_medicine(20)