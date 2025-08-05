from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Medicine, MedicineAction
from .forms import MedicineForm
import csv
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from datetime import datetime
from django.db import IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



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

    recent_actions = MedicineAction.objects.select_related('medicine').order_by('-timestamp')[:5]
    return render(request, 'Medicine_inventory/view_medicine.html', {
        'medicine': filtered,
        'categories': categories,
        'recent_actions' : recent_actions,
    })

def view_medicine_table(request):
    medicines = Medicine.objects.all()
    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

    # Sorting
    sort_by = request.GET.get('sort', 'name') # Default sort by name
    direction = request.GET.get('dir', 'asc') # Default direction ascending

    if sort_by not in ['name', 'quantity_in_stock']: # Whitelist sortable fields
        sort_by = 'name'

    order = sort_by if direction == 'asc' else f'-{sort_by}'
    medicines = medicines.order_by(order)

    # Filtering (applied after sorting)
    search_query = request.GET.get('search')
    category = request.GET.get('category')
    expiry = request.GET.get('expiry')
    low_stock = request.GET.get('low_stock')

    if search_query:
        medicines = medicines.filter(name__icontains=search_query)

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

    recent_actions = MedicineAction.objects.select_related('medicine').order_by('-timestamp')[:5]
    
    # Pass sorting info to the template
    context = {
        'medicine': filtered,
        'categories': categories,
        'recent_actions': recent_actions,
        'current_sort': sort_by,
        'current_dir': direction,
    }
    return render(request, 'Medicine_inventory/medicine_table.html', context)

# Create a new medicine entry
def create_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            med_code = form.cleaned_data['med_code']
            batch_date_int = int(form.cleaned_data['batch_date'])
            supplier_code = form.cleaned_data['supplier_code']
            seq = form.cleaned_data['seq']
            batch_number = f"{med_code}-{batch_date_int}-{supplier_code}-{seq}"

            medicine = form.save(commit=False)
            medicine.batch_number = batch_number
            
            try:
                medicine.save()
                MedicineAction.objects.create(
                    medicine=medicine,
                    medicine_name=medicine.name,
                    batch_number=medicine.batch_number,
                    action='created'
                )
                messages.success(request, f"Successfully registered new medication: '{medicine.name}'.")
                return redirect('medicine_table')
            except IntegrityError:
                form.add_error(None, "A medicine with this batch number already exists. Please change the batch details.")
    else:
        form = MedicineForm()
    return render(request, 'Medicine_inventory/create_medicine.html', {'form': form})

# Delete a medicine
def delete_medicine(request, id):
    medicine = get_object_or_404(Medicine, pk=id)
    medicine_name = medicine.name
    
    MedicineAction.objects.create(
        medicine=medicine,
        medicine_name=medicine.name,
        batch_number=medicine.batch_number,
        action='deleted'
    )
    medicine.delete()
    
    messages.success(request, f"The record for '{medicine_name}' has been deleted successfully.")
    
    return redirect('medicine_table')

# Update a medicine
def update_medicine(request, id):
    medicine = get_object_or_404(Medicine, pk=id)
    initial = {}
    if medicine.batch_number:
        parts = medicine.batch_number.split('-')
        if len(parts) == 4:
            initial = {
                'med_code': parts[0],
                'batch_date': str(parts[1]),
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
            
            MedicineAction.objects.create(
                medicine=medicine,
                medicine_name=medicine.name,
                batch_number=medicine.batch_number,
                action='updated'
            )
            
            messages.success(request, f"The record for '{medicine.name}' has been updated successfully.")
            
            return redirect('medicine_table')
    else:
        form = MedicineForm(instance=medicine, initial=initial)
    return render(request, 'Medicine_inventory/update_medicine.html', {'form': form, 'medicine': medicine})

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

def export_medicine_pdf(request):
    medicines = Medicine.objects.all()
    html_string = render_to_string('Medicine_inventory/medicine_pdf.html', {
        'medicines': medicines,
        'now': datetime.now()
    })
    pdf_file = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="medicine_inventory.pdf"'
    return response

def med_inventory_dashboard(request):
    medicines = Medicine.objects.all()
    total_medicines = medicines.count()
    low_stock_count = sum(1 for m in medicines if m.quantity_in_stock < m.reorder_level)
    near_expiry_count = sum(1 for m in medicines if hasattr(m, 'is_near_expiry') and m.is_near_expiry())
    expired_count = sum(1 for m in medicines if hasattr(m, 'is_expired') and m.is_expired())
    recent_medicines = medicines.order_by('-id')[:8]

    # For chart
    from collections import Counter
    category_counts_dict = Counter(m.category for m in medicines)
    category_labels = list(category_counts_dict.keys())
    category_counts = list(category_counts_dict.values())

    # Fetch ALL actions, ordered by the most recent
    action_list = MedicineAction.objects.select_related('medicine').order_by('-timestamp')
    
    # Set up the Paginator
    paginator = Paginator(action_list, 10) # Show 10 actions per page
    page_number = request.GET.get('page')
    
    try:
        actions_page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        actions_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver the last page of results.
        actions_page = paginator.page(paginator.num_pages)

    context = {
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'near_expiry_count': near_expiry_count,
        'expired_count': expired_count,
        'recent_medicines': recent_medicines,
        'category_labels': category_labels,
        'category_counts': category_counts,
        'recent_actions': actions_page, # Use the paginated object
    }
    return render(request, 'Medicine_inventory/med_inventory_dash.html', context)

