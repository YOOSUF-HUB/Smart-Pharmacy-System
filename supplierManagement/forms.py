from django import forms
from .models import Supplier, Product
from django.core.exceptions import ValidationError

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "name", "contact_person", "email", "phone", "address",
            "supplier_type", "products_supplied", "license_number", "tax_id",
            "payment_terms", "bank_details", "status", "products"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter supplier name"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter contact person"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter email address"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter phone number"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Enter address"}),
            "supplier_type": forms.Select(attrs={"class": "form-select"}),
            "products_supplied": forms.Select(attrs={"class": "form-select"}),
            "license_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter license number"}),
            "tax_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter tax/registration number"}),
            "payment_terms": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Net 30, Net 60, COD"}),
            "bank_details": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Enter bank details"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "products": forms.SelectMultiple(attrs={"class": "form-select select2", "multiple": "multiple"}),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Supplier name is required.")
        return name

    def clean_contact_person(self):
        contact_person = self.cleaned_data.get("contact_person", "").strip()
        return contact_person

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone and (not phone.isdigit() or len(phone) < 7 or len(phone) > 15):
            raise ValidationError("Phone number must be between 7 and 15 digits and contain only numbers.")
        return phone

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter product name"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }