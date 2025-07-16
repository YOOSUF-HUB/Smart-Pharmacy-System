from django.contrib import messages
from django.shortcuts import render, redirect
from Medicine_inventory.models import Medicine
from Medicine_inventory.forms import MedicineForm
from django.shortcuts import render, redirect, get_object_or_404

# View all medicines
def view_medicine(request):
    medicine = Medicine.objects.all()
    return render(request, 'Medicine_inventory/view_medicine.html', {'medicine': medicine})

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