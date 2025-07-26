from django.test import TestCase
from .models import Medicine

class MedicineModelTest(TestCase):
    def test_create_medicine(self):
        medicine = Medicine.objects.create(
            name="Aspirin",
            brand="Sanofi",
            category="Painkiller",
            description="Pain relief",
            dosage="100mg",
            price=100,
            quantity_in_stock=50,
            reorder_level=10,
            manufacture_date="2025-01-01",
            expiry_date="2027-01-01",
            supplier="Cardinal",
            batch_number="ASPIR-20250101-CARDINAL-008"
        )
        self.assertEqual(medicine.name, "Aspirin")