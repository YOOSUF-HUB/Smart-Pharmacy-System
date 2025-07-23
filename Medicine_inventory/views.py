from django.contrib import messages
from django.shortcuts import render, redirect
from Medicine_inventory.models import Medicine
from Medicine_inventory.forms import MedicineForm
from django.shortcuts import render, redirect, get_object_or_404

# View all medicines
def view_medicine(request):
    medicine = Medicine.objects.all()
    for med in medicine:
        med.low_stock = med.quantity_in_stock < med.reorder_level
        med.near_expiry = med.is_near_expiry()
    return render(request, 'Medicine_inventory/view_medicine.html', {'medicine': medicine})

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
            form.save()
            messages.success(request, 'Medicine added successfully!')
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
    medicine = get_object_or_404(Medicine, id=id)

    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            return redirect('medicine_list')  # Adjust the URL name accordingly
    else:
        form = MedicineForm(instance=medicine)

    return render(request, 'Medicine_inventory/update_medicine.html', {'form': form})

# Home view
def home(request):
    return render(request, 'crudApp/home.html')