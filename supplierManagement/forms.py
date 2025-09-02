from django import forms
from .models import Supplier, Product
from django.core.exceptions import ValidationError

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_person", "phone", "email", "address", "products", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter supplier name"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter contact person"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter phone number"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter email address"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Enter address"}),
            "products": forms.SelectMultiple(attrs={"class": "form-select select2", "multiple": "multiple"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    # Custom validation for supplier name
    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Supplier name is required.")
        if not all(char.isalpha() or char.isspace() for char in name):
            raise ValidationError("Supplier name must contain only letters and spaces.")
        return name

    # Custom validation for contact person
    def clean_contact_person(self):
        contact_person = self.cleaned_data.get("contact_person", "").strip()
        if contact_person and not all(char.isalpha() or char.isspace() for char in contact_person):
            raise ValidationError("Contact person must contain only letters and spaces.")
        return contact_person
    
    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if len(phone) < 10 or len(phone) > 15:
            raise ValidationError("Phone number must be between 10 and 15 digits.")
        return phone

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter product name"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }