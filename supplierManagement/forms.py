from django import forms
from django.core.exceptions import ValidationError
from .models import Supplier, Product, PurchaseOrder, PurchaseOrderItem
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

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [f.name for f in PurchaseOrder._meta.fields if f.editable and f.name not in ("id", "total_cost")]
        widgets = {
            "expected_delivery": forms.DateInput(attrs={"type": "date"}),
        }

class PurchaseOrderItemForm(forms.ModelForm):
    product_name = forms.CharField(
        label="Product",
        widget=forms.TextInput(attrs={
            "placeholder": "Type product name",
            "autocomplete": "off",
            "list": "product-list",
        })
    )

    class Meta:
        model = PurchaseOrderItem
        fields = ["product_name", "quantity", "price"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "price": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill product_name from existing item
        if self.instance and self.instance.pk:
            # Use product_name field first, fallback to product FK
            if hasattr(self.instance, 'product_name') and self.instance.product_name:
                self.fields["product_name"].initial = self.instance.product_name
            elif getattr(self.instance, "product_id", None):
                self.fields["product_name"].initial = self.instance.product.name

    def clean_product_name(self):
        name = (self.cleaned_data.get("product_name") or "").strip()
        if not name:
            raise ValidationError("Enter a product name.")
        # Auto-create product if doesn't exist
        product, _created = Product.objects.get_or_create(name=name)
        self._resolved_product = product
        return name

    def clean(self):
        cleaned = super().clean()
        # Set product FK before model validation
        if getattr(self, "_resolved_product", None):
            self.instance.product = self._resolved_product
            self.instance.product_name = self.cleaned_data.get("product_name", "")
        return cleaned

    def save(self, commit=True):
        # product and product_name already set in clean()
        return super().save(commit=commit)

class PurchaseOrderStatusForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["status"]