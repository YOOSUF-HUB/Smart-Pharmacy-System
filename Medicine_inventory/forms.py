from django import forms
from .models import Medicine

class MedicineForm(forms.ModelForm):
    med_code = forms.CharField(
        max_length=5,
        required=True,
        label="Medicine Code",
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'})
    )
    batch_date = forms.CharField(max_length=8, required=True, label="Batch Date", widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))
    supplier_code = forms.CharField(max_length=20, required=True, label="Supplier Code", widget=forms.TextInput(attrs={'placeholder': 'SUPPLIER', 'class': 'form-control'}))
    seq = forms.CharField(max_length=5, required=True, label="Sequence", widget=forms.TextInput(attrs={'placeholder': 'SEQ', 'class': 'form-control'}))

    class Meta:
        model = Medicine
        exclude = ['batch_number']
        widgets = {
            'manufacture_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }




