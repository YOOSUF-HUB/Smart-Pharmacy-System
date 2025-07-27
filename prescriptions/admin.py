# prescriptions/admin.py

from django.contrib import admin
from .models import Patient, Doctor, Prescription, PrescriptionItem, DrugInteraction

# Register your models here to make them accessible in the Django admin interface.

# Customize the display of the Patient model in the admin.
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    # Fields to display in the list view of patients.
    list_display = ('id', 'first_name', 'last_name', 'date_of_birth', 'contact_number')
    # Fields to search by in the admin search bar.
    search_fields = ('first_name', 'last_name', 'contact_number')
    # Fields to filter by in the right sidebar of the admin list view.
    list_filter = ('date_of_birth',)
    # Default ordering for the list view.
    ordering = ('last_name', 'first_name')

# Customize the display of the Doctor model in the admin.
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    # Fields to display in the list view of doctors.
    list_display = ('id', 'first_name', 'last_name', 'specialization', 'contact_number')
    # Fields to search by.
    search_fields = ('first_name', 'last_name', 'specialization')
    # Fields to filter by.
    list_filter = ('specialization',)
    # Default ordering.
    ordering = ('last_name', 'first_name')

# Inline for PrescriptionItem to allow adding/editing items directly within the Prescription form.
class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    # Number of extra forms to display for adding new items.
    extra = 1
    # Fields to display in the inline form.
    fields = ('medicine', 'dosage', 'duration', 'requested_quantity', 'dispensed_quantity')
    # Make dispensed_quantity readonly in admin as it's updated by logic.
    readonly_fields = ('dispensed_quantity',)


# Customize the display of the Prescription model in the admin.
@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    # Fields to display in the list view of prescriptions.
    list_display = ('id', 'patient', 'doctor', 'prescription_date', 'is_validated', 'interaction_warning_summary')
    # Fields to search by.
    search_fields = ('patient__first_name', 'patient__last_name', 'doctor__first_name', 'doctor__last_name', 'notes')
    # Fields to filter by.
    list_filter = ('prescription_date', 'is_validated', 'doctor', 'patient')
    # Default ordering.
    ordering = ('-prescription_date',)
    # Add the inline for PrescriptionItem to allow managing items directly.
    inlines = [PrescriptionItemInline]

    # Custom method to display a summary of the interaction warning in the list view.
    def interaction_warning_summary(self, obj):
        if obj.interaction_warning:
            # Display first 50 characters or full warning if shorter.
            return obj.interaction_warning[:50] + '...' if len(obj.interaction_warning) > 50 else obj.interaction_warning
        return "No warning"
    interaction_warning_summary.short_description = "Interaction Warning" # Column header name


# Customize the display of the DrugInteraction model in the admin.
@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    # Fields to display in the list view of drug interactions.
    list_display = ('id', 'drug1_name', 'drug2_name', 'severity', 'interaction_description_summary')
    # Fields to search by.
    search_fields = ('drug1_name', 'drug2_name', 'interaction_description')
    # Fields to filter by.
    list_filter = ('severity',)
    # Default ordering.
    ordering = ('severity', 'drug1_name')

    # Custom method to display a summary of the interaction description.
    def interaction_description_summary(self, obj):
        if obj.interaction_description:
            return obj.interaction_description[:75] + '...' if len(obj.interaction_description) > 75 else obj.interaction_description
        return "N/A"
    interaction_description_summary.short_description = "Description" # Column header name

