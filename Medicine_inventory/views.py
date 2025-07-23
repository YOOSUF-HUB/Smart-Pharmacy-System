from django.contrib import messages
from django.shortcuts import render, redirect
from Medicine_inventory.models import Medicine
from Medicine_inventory.forms import MedicineForm
from django.shortcuts import render, redirect, get_object_or_404
import csv
from django.http import HttpResponse

# View all medicines
def view_medicine(request):
    medicines = Medicine.objects.all()
    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

    # Filtering
    category = request.GET.get('category')
    expiry = request.GET.get('expiry')
    low_stock = request.GET.get('low_stock')

    if category:
        medicines = medicines.filter(category=category)
    filtered = []
    for med in medicines:
        med.low_stock = med.quantity_in_stock < med.reorder_level
        med.near_expiry = med.is_near_expiry()
        med.is_expired = med.is_expired()
        if expiry == 'near' and not med.near_expiry:
            continue
        if expiry == 'expired' and not med.is_expired:
            continue
        if low_stock == 'low' and not med.low_stock:
            continue
        filtered.append(med)
    return render(request, 'Medicine_inventory/view_medicine.html', {
        'medicine': filtered,
        'categories': categories,
    })

def view_medicine_cards(request):
    medicines = Medicine.objects.all()
    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

    # Filtering
    category = request.GET.get('category')
    expiry = request.GET.get('expiry')
    low_stock = request.GET.get('low_stock')

    if category:
        medicines = medicines.filter(category=category)
    filtered = []
    for med in medicines:
        med.low_stock = med.quantity_in_stock < med.reorder_level
        med.near_expiry = med.is_near_expiry()
        med.is_expired = med.is_expired()
        if expiry == 'near' and not med.near_expiry:
            continue
        if expiry == 'expired' and not med.is_expired:
            continue
        if low_stock == 'low' and not med.low_stock:
            continue
        filtered.append(med)
    return render(request, 'Medicine_inventory/view_medicine.html', {
        'medicine': filtered,
        'categories': categories,
    })

def view_medicine_table(request):
    medicines = Medicine.objects.all()
    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

    # Filtering
    category = request.GET.get('category')
    expiry = request.GET.get('expiry')
    low_stock = request.GET.get('low_stock')

    if category:
        medicines = medicines.filter(category=category)
    filtered = []
    for med in medicines:
        med.low_stock = med.quantity_in_stock < med.reorder_level
        med.near_expiry = med.is_near_expiry()
        med.is_expired = med.is_expired()
        # Expiry filter
        if expiry == 'near' and not med.near_expiry:
            continue
        if expiry == 'expired' and not med.is_expired:
            continue
        # Low stock filter
        if low_stock == 'low' and not med.low_stock:
            continue
        filtered.append(med)
    return render(request, 'Medicine_inventory/medicine_table.html', {
        'medicine': filtered,
        'categories': categories,
    })

# Create a new medicine entry
def create_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            med_code = form.cleaned_data['med_code']
            batch_date_int = int(form.cleaned_data['batch_date'])  # Directly convert to integer
            supplier_code = form.cleaned_data['supplier_code']
            seq = form.cleaned_data['seq']
            batch_number = f"{med_code}-{batch_date_int}-{supplier_code}-{seq}"

            medicine = form.save(commit=False)
            medicine.batch_number = batch_number
            medicine.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'Medicine_inventory/create_medicine.html', {'form': form})

# Delete a medicine
def delete_medicine(request, id):
    medicine = Medicine.objects.get(id=id)
    medicine.delete()
    return redirect('medicine_list')

# Update a medicine
def update_medicine(request, id):
    medicine = get_object_or_404(Medicine, pk=id)
    initial = {}
    if medicine.batch_number:
        parts = medicine.batch_number.split('-')
        if len(parts) == 4:
            initial = {
                'med_code': parts[0],
                'batch_date': str(parts[1]),  # This will be an integer string like '20250723'
                'supplier_code': parts[2],
                'seq': parts[3],
            }
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            med_code = form.cleaned_data['med_code']
            batch_date_int = int(form.cleaned_data['batch_date'])
            supplier_code = form.cleaned_data['supplier_code']
            seq = form.cleaned_data['seq']
            batch_number = f"{med_code}-{batch_date_int}-{supplier_code}-{seq}"
            medicine = form.save(commit=False)
            medicine.batch_number = batch_number
            medicine.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine, initial=initial)
    return render(request, 'Medicine_inventory/update_medicine.html', {'form': form})

# Home view
def home(request):
    return render(request, 'crudApp/home.html')

def export_medicine_csv(request):
    medicines = Medicine.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="medicine_inventory.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Name', 'Brand', 'Category', 'Description', 'Dosage', 'Price',
        'Quantity In Stock', 'Reorder Level', 'Manufacture Date', 'Expiry Date',
        'Batch Number', 'Supplier'
    ])
    for med in medicines:
        writer.writerow([
            med.name, med.brand, med.category, med.description, med.dosage, med.price,
            med.quantity_in_stock, med.reorder_level, med.manufacture_date, med.expiry_date,
            med.batch_number, med.supplier
        ])
    return response