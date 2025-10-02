from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Medicine
import re

class MedicineForm(forms.ModelForm):
    med_code = forms.CharField(
        max_length=5,
        required=True,
        label="Medicine Code",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    batch_date = forms.CharField(
        max_length=8,
        required=True,
        label="Batch Date",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    supplier_code = forms.CharField(
        max_length=20,
        required=True,
        label="Supplier Code",
        widget=forms.TextInput(attrs={'placeholder': 'SUPPLIER', 'class': 'form-control'})
    )
    seq_number = forms.CharField(
        max_length=5,
        required=True,
        label="Sequence",
        widget=forms.TextInput(attrs={'placeholder': 'SEQ', 'class': 'form-control'})
    )

    class Meta:
        model = Medicine
        fields = [
            'name', 'brand', 'category', 'medicine_type', 'description', 
            'dosage', 'cost_price', 'selling_price', 'image', 
            'quantity_in_stock', 'reorder_level', 'manufacture_date', 
            'expiry_date', 'batch_number', 'supplier',
            # Add any batch generation fields if you have them
        ]
        widgets = {
            'manufacture_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500'
                }
            ),
            'expiry_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500'
                }
            ),
            'batch_number': forms.TextInput(attrs={'readonly': 'readonly'}),
            'medicine_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Defensive: only proceed if custom fields exist
        bn = (self.instance.batch_number or "").strip()
        if bn and all(f in self.fields for f in ('med_code','batch_date','supplier_code','seq_number')):
            normalized = re.sub(r'-{2,}', '-', bn.upper())
            parts = normalized.split('-')
            # accept exactly 4 non-empty segments
            if len(parts) == 4 and all(parts):
                self.fields['med_code'].initial = parts[0]
                self.fields['batch_date'].initial = parts[1]
                self.fields['supplier_code'].initial = parts[2]
                self.fields['seq_number'].initial = parts[3]
            else:
                # leave blank so user can repair
                pass

    def clean(self):
        cleaned = super().clean()
        mc = (cleaned.get('med_code') or '').strip().upper()
        bd = (cleaned.get('batch_date') or '').strip()
        sc = (cleaned.get('supplier_code') or '').strip().upper()
        sq = (cleaned.get('seq_number') or '').strip()
        # If any provided but not all, do not overwrite existing batch_number
        if mc and bd and sc and sq:
            # normalize
            mc = re.sub(r'-+','-', mc)
            sc = re.sub(r'-+','-', sc)
            # zero-pad sequence to 3
            if sq.isdigit():
                sq = sq.zfill(3)
            cleaned['batch_number'] = f"{mc}-{bd}-{sc}-{sq}"
        return cleaned

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

    def clean_batch_number(self):
        batch_number = self.cleaned_data.get('batch_number')
        
        if batch_number:
            # Check if batch number already exists (excluding current instance in update)
            existing = Medicine.objects.filter(batch_number=batch_number)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f"A medicine with batch number '{batch_number}' already exists. "
                    "Batch numbers must be unique."
                )
        
        return batch_number
    
    def clean_manufacture_date(self):
        manufacture_date = self.cleaned_data.get('manufacture_date')
        
        if manufacture_date:
            if manufacture_date > date.today():
                raise ValidationError(
                    "Manufacture date cannot be in the future."
                )
        
        return manufacture_date
    
    def clean(self):
        cleaned_data = super().clean()
        manufacture_date = cleaned_data.get('manufacture_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        # Validate expiry date is after manufacture date
        if manufacture_date and expiry_date:
            if expiry_date <= manufacture_date:
                raise ValidationError({
                    'expiry_date': 'Expiry date must be after manufacture date.'
                })
        
        return cleaned_data


class BulkUploadForm(forms.Form):
    csv_file = forms.FileField(label="CSV File")
