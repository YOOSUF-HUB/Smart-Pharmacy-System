# prescriptions/forms.py

from django import forms
from .models import Patient, Doctor, Prescription, PrescriptionItem, DrugInteraction
# Import the Medicine model from the Medicine_Inventory app
from Medicine_inventory.models import Medicine

# Form for creating and updating Patient instances.
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        # Include all fields from the Patient model
        fields = '__all__'
        # Add widgets for better user experience, especially for date input
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patient First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patient Last Name'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +1234567890'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Patient Address'}),
        }
        # Labels for form fields
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'date_of_birth': 'Date of Birth',
            'contact_number': 'Contact Number',
            'address': 'Address',
        }

# Form for creating and updating Doctor instances.
class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        # Include all fields from the Doctor model
        fields = '__all__'
        # Add widgets for better user experience
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doctor First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doctor Last Name'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., General Practitioner'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +1234567890'}),
        }
        # Labels for form fields
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'specialization': 'Specialization',
            'contact_number': 'Contact Number',
        }

# Form for creating and updating Prescription instances.
class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        # We exclude 'prescription_date', 'is_validated', 'interaction_warning'
        # as these are either auto-set or handled by the system/DL model.
        fields = ['patient', 'doctor', 'notes']
        # Add widgets for better user experience
        widgets = {
            # Use Select widget for ForeignKey fields (Patient, Doctor)
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Any additional notes for the prescription'}),
        }
        # Labels for form fields
        labels = {
            'patient': 'Select Patient',
            'doctor': 'Select Doctor',
            'notes': 'Prescription Notes',
        }

# Form for creating and updating PrescriptionItem instances.
# This form is crucial for adding medicines to a prescription.
class PrescriptionItemForm(forms.ModelForm):
    # Override the medicine field to use a ModelChoiceField for better control
    # and to ensure it pulls from the Medicine_Inventory.Medicine model.
    # The queryset fetches all available medicines (batches) from the inventory.
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.all().order_by('name', 'batch_number'),
        label="Select Medicine (Batch)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PrescriptionItem
        # We exclude 'prescription' as it will be set in the view based on the URL.
        # 'dispensed_quantity' will be handled by logic, not direct user input in this form.
        fields = ['medicine', 'dosage', 'duration', 'requested_quantity']
        # Add widgets for better user experience
        widgets = {
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg, twice daily'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 7 days, until finished'}),
            'requested_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Quantity requested by patient'}),
        }
        # Labels for form fields
        labels = {
            'medicine': 'Medicine',
            'dosage': 'Dosage Instructions',
            'duration': 'Duration of Use',
            'requested_quantity': 'Requested Quantity',
        }

    # Custom validation for requested_quantity (optional, but good for early checks)
    def clean_requested_quantity(self):
        requested_quantity = self.cleaned_data['requested_quantity']
        if requested_quantity <= 0:
            raise forms.ValidationError("Requested quantity must be at least 1.")
        return requested_quantity

# Form for DrugInteraction (for future DL model population/management)
class DrugInteractionForm(forms.ModelForm):
    class Meta:
        model = DrugInteraction
        fields = '__all__'
        widgets = {
            'drug1_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Drug Name'}),
            'drug2_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Second Drug Name'}),
            'interaction_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description of the interaction'}),
            'severity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mild, Moderate, Severe'}),
        }
        labels = {
            'drug1_name': 'Drug 1 Name',
            'drug2_name': 'Drug 2 Name',
            'interaction_description': 'Interaction Description',
            'severity': 'Severity',
        }

