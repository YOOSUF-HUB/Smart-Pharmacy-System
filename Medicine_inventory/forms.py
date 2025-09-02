from django import forms
from .models import Medicine

class MedicineForm(forms.ModelForm):
    med_code = forms.CharField(
        max_length=5,
        required=True,
        label="Medicine Code",
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'})
    )
    batch_date = forms.CharField(
        max_length=8,
        required=True,
        label="Batch Date",
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'})
    )
    supplier_code = forms.CharField(
        max_length=20,
        required=True,
        label="Supplier Code",
        widget=forms.TextInput(attrs={'placeholder': 'SUPPLIER', 'class': 'form-control'})
    )
    seq = forms.CharField(
        max_length=5,
        required=True,
        label="Sequence",
        widget=forms.TextInput(attrs={'placeholder': 'SEQ', 'class': 'form-control'})
    )

    class Meta:
        model = Medicine
        exclude = ['batch_number']
        widgets = {
            'manufacture_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        cost_price = cleaned_data.get('cost_price')
        selling_price = cleaned_data.get('selling_price')

        if cost_price and selling_price and cost_price > selling_price:
            raise forms.ValidationError(
                "Cost price (Rs. %(cost)s) is greater than selling price (Rs. %(selling)s). This will result in a loss.",
                params={'cost': cost_price, 'selling': selling_price},
                code='negative_margin'
            )

        # Combine the batch fields into batch_number
        med_code = cleaned_data.get('med_code', '').strip()
        batch_date = cleaned_data.get('batch_date', '').strip()
        supplier_code = cleaned_data.get('supplier_code', '').strip()
        seq = cleaned_data.get('seq', '').strip()
        if med_code and batch_date and supplier_code and seq:
            cleaned_data['batch_number'] = f"{med_code}-{batch_date}-{supplier_code}-{seq}"
        else:
            raise forms.ValidationError("All batch number components are required.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set the batch_number field from the cleaned_data
        batch_number = self.cleaned_data.get('batch_number')
        if batch_number:
            instance.batch_number = batch_number
        if commit:
            instance.save()
            self.save_m2m()
        return instance




