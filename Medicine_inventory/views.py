import base64
import csv
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, F, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from django.db.models import ProtectedError

from .forms import MedicineForm
from .models import Medicine, MedicineAction
from Non_Medicine_inventory.models import NonMedicalProduct
from supplierManagement.models import Supplier  # Adjust this import to your actual Supplier model location



# Role check decorator
def pharmacist_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "pharmacist")(view_func)


# -------------------- Medicine Views --------------------

# @pharmacist_required
# def view_medicine(request):
#     medicines = Medicine.objects.all()
#     categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

#     category = request.GET.get('category')
#     expiry = request.GET.get('expiry')
#     low_stock = request.GET.get('low_stock')

#     if category:
#         medicines = medicines.filter(category=category)

#     filtered = []
#     for med in medicines:
#         med.low_stock = med.quantity_in_stock < med.reorder_level
#         med.near_expiry = med.is_near_expiry()
#         med.is_expired = med.is_expired()
#         if expiry == 'near' and not med.near_expiry:
#             continue
#         if expiry == 'expired' and not med.is_expired:
#             continue
#         if low_stock == 'low' and not med.low_stock:
#             continue
#         filtered.append(med)

#     return render(request, 'Medicine_inventory/view_medicine.html', {
#         'medicine': filtered,
#         'categories': categories,
#     })


@pharmacist_required
def view_medicine_cards(request):
    """
    Cards view with server-side search by name/brand/supplier/description and filters.
    """
    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

    # Base queryset (ordered)
    qs = Medicine.objects.all().order_by('name')

    # GET params (safe defaults)
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category')
    expiry = request.GET.get('expiry')
    low_stock = request.GET.get('low_stock')
    # normalize the available_online param
    online = request.GET.get('available_online', '').strip().lower()

    # Apply search (case-insensitive). Handle supplier as FK (supplier__name) or text field.
    if search:
        # detect if supplier is a ForeignKey on the Medicine model and adjust lookup accordingly
        try:
            from django.db.models import ForeignKey
            supplier_field = Medicine._meta.get_field('supplier')
            supplier_is_fk = isinstance(supplier_field, ForeignKey)
        except Exception:
            supplier_is_fk = False

        supplier_lookup = 'supplier__name__icontains' if supplier_is_fk else 'supplier__icontains'

        qs = qs.filter(
            Q(name__icontains=search) |
            Q(brand__icontains=search) |
            Q(description__icontains=search) |
            Q(**{supplier_lookup: search})
        )

    # Apply category filter
    if category:
        qs = qs.filter(category=category)

    # NEW: Apply available_online filter (supports multiple common values)
    if online in ('online', 'true', '1'):
        qs = qs.filter(available_online=True)
    elif online in ('offline', 'false', '0'):
        qs = qs.filter(available_online=False)

    # Build filtered list applying computed properties and expiry/low-stock filters
    filtered = []
    for med in qs:
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
        'recent_actions': recent_actions,
        'available_online': online,
    })
# ...existing code...


@pharmacist_required
def view_medicine_table(request):
    medicines = Medicine.objects.all()
    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

    # Sorting
    sort_by = request.GET.get('sort', 'name')
    direction = request.GET.get('dir', 'asc')
    if sort_by not in ['name', 'quantity_in_stock']:
        sort_by = 'name'
    order = sort_by if direction == 'asc' else f'-{sort_by}'
    medicines = medicines.order_by(order)

    # Filtering
    search_query = request.GET.get('search', '').strip()
    category = request.GET.get('category')
    expiry = request.GET.get('expiry')
    low_stock = request.GET.get('low_stock')
    # normalize available_online values
    available_online = request.GET.get('available_online', '').strip().lower()

    if search_query:
        medicines = medicines.filter(name__icontains=search_query)
    if category:
        medicines = medicines.filter(category=category)

    # Apply available_online filter if provided
    if available_online in ('online', 'true', '1'):
        medicines = medicines.filter(available_online=True)
    elif available_online in ('offline', 'false', '0'):
        medicines = medicines.filter(available_online=False)

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

    context = {
        'medicine': filtered,
        'categories': categories,
        'recent_actions': recent_actions,
        'current_sort': sort_by,
        'current_dir': direction,
        'available_online': available_online,  # pass to template for UI state
    }
    return render(request, 'Medicine_inventory/medicine_table.html', context)


@pharmacist_required
def create_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                medicine = form.save()
                MedicineAction.objects.create(
                    medicine=medicine,
                    action='Added',
                    user=request.user
                )
                messages.success(request, f"Successfully registered new medication: '{medicine.name}'.")
                return redirect('medicine_table')
            except ValidationError as e:
                # Handle model validation errors
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
        else:
            # Form validation failed
            messages.error(request, "Please correct the errors below.")
    else:
        form = MedicineForm()
    return render(request, 'Medicine_inventory/create_medicine.html', {'form': form})


@pharmacist_required
def delete_medicine(request, id):
    medicine = get_object_or_404(Medicine, pk=id)
    
    if request.method == 'POST':
        try:
            medicine_name = medicine.name
            medicine_batch = medicine.batch_number
            medicine.delete()
            messages.success(request, f'Medicine "{medicine_name}" (Batch: {medicine_batch}) has been successfully deleted from inventory.')
            return redirect('medicine_cards')  # Changed to redirect to cards view
        except ProtectedError as e:
            # Extract the related objects information
            protected_objects = e.protected_objects
            related_models = set()
            related_count = 0
            
            for obj in protected_objects:
                model_name = obj._meta.verbose_name
                related_models.add(model_name)
                related_count += 1
            
            # Create user-friendly error message
            models_list = ', '.join(related_models)
            error_message = f'''
            <strong>Cannot delete "{medicine.name}" (Batch: {medicine.batch_number})</strong><br><br>
            <div class="bg-amber-50 border-l-4 border-amber-400 p-4 my-3 rounded">
                <div class="flex">
                    <div class="ml-3">
                        <p class="text-sm text-amber-700">
                            <strong>Reason:</strong> This medicine is currently referenced in {related_count} record(s) 
                            including: <strong>{models_list}</strong>
                        </p>
                        <p class="text-sm text-amber-700 mt-2">
                            <strong>What this means:</strong> This medicine has been used in prescriptions or sales transactions 
                            and cannot be deleted to maintain data integrity.
                        </p>
                    </div>
                </div>
            </div>
            <div class="bg-blue-50 border-l-4 border-blue-400 p-4 my-3 rounded">
                <div class="flex">
                    <div class="ml-3">
                        <p class="text-sm text-blue-700">
                            <strong>Suggested actions:</strong>
                        </p>
                        <ul class="text-sm text-blue-700 mt-1 list-disc list-inside">
                            <li>Set the medicine quantity to 0 to mark it as out of stock</li>
                            <li>Update the medicine status or add a note indicating it's discontinued</li>
                            <li>Contact the system administrator if you need to remove this medicine entirely</li>
                        </ul>
                    </div>
                </div>
            </div>
            '''
            
            messages.error(request, error_message)
            return redirect('medicine_cards')  # Changed to redirect to cards view
    
    # If GET request, redirect to cards view
    return redirect('medicine_table')


@pharmacist_required
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
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            try:
                medicine = form.save()
                MedicineAction.objects.create(
                    medicine=medicine,
                    action='Updated',
                    user=request.user
                )
                messages.success(request, f"The record for '{medicine.name}' has been updated successfully.")
                return redirect('medicine_table')
            except ValidationError as e:
                # Handle model validation errors
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MedicineForm(instance=medicine, initial=initial)

    return render(request, 'Medicine_inventory/update_medicine.html', {'form': form, 'medicine': medicine})


# -------------------- Export Views --------------------

@pharmacist_required
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
            med.name, med.brand, med.category, med.description, med.dosage,
            med.selling_price, med.cost_price, med.quantity_in_stock,
            med.reorder_level, med.manufacture_date, med.expiry_date,
            med.batch_number, med.supplier
        ])
    return response

@pharmacist_required
def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    recent_actions = MedicineAction.objects.filter(medicine=medicine).order_by('-timestamp')[:15]
    profit = None
    margin_pct = None
    try:
        if medicine.cost_price is not None and medicine.selling_price is not None:
            profit = medicine.selling_price - medicine.cost_price
            if medicine.cost_price and medicine.cost_price > 0:
                margin_pct = (profit / medicine.cost_price) * Decimal('100')
    except (InvalidOperation, ZeroDivisionError):
        profit = None
        margin_pct = None
    context = {
        'medicine': medicine,
        'recent_actions': recent_actions,
        'profit': profit,
        'margin_pct': margin_pct,
    }
    return render(request, 'Medicine_inventory/medicine_detail.html', context)

@pharmacist_required
def export_medicine_pdf(request):
    medicines = Medicine.objects.all()
    total_medicines = medicines.count()
    low_stock_count = Medicine.objects.filter(quantity_in_stock__lt=F('reorder_level')).count()
    expired = medicines.filter(expiry_date__lt=timezone.now().date()).count()

    logo_file = os.path.join(settings.BASE_DIR, 'static/MediSyn_Logo/1.png')
    with open(logo_file, 'rb') as f:
        logo_data = base64.b64encode(f.read()).decode('utf-8')

    context = {
        'medicines': medicines,
        'now': timezone.now(),
        'logo_data': logo_data,
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'expired': expired,
    }

    html_string = render_to_string('Medicine_inventory/medicine_pdf.html', context)
    pdf_file = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="medicine_inventory.pdf"'
    return response


# -------------------- Dashboard --------------------

@pharmacist_required
def med_inventory_dash(request):
    today = timezone.now().date()
    expiry_threshold = today + timezone.timedelta(days=8)

    total_medicines = Medicine.objects.count()
    low_stock_count = Medicine.objects.filter(quantity_in_stock__lt=F('reorder_level')).count()
    near_expiry_count = Medicine.objects.filter(expiry_date__gt=today, expiry_date__lte=expiry_threshold).count()
    expired_count = Medicine.objects.filter(expiry_date__lt=today).count()

    total_nonmedical = NonMedicalProduct.objects.count()
    nonmedical_low_stock_count = NonMedicalProduct.objects.filter(stock__lt=F('reorder_level')).count()
    nonmedical_active_count = NonMedicalProduct.objects.filter(available_online=True).count()
    nonmedical_categories_count = NonMedicalProduct.objects.values('category').distinct().count()


    # Add online orders statistics
    try:
        from onlineStore.models import Order
        pending_orders_count = Order.objects.filter(status='Pending').count()
        processing_orders_count = Order.objects.filter(status='Processing').count()
        total_orders_today = Order.objects.filter(created_at__date=today).count()
        total_orders = Order.objects.count()
        recent_orders = Order.objects.all().order_by('-created_at')[:5]
    except ImportError:
        # Fallback if Order model not found
        pending_orders_count = 0
        processing_orders_count = 0
        total_orders_today = 0
        total_orders = 0
        recent_orders = []

    category_data = Medicine.objects.values('category').annotate(count=Count('id')).order_by('-count')
    category_labels = [item['category'] for item in category_data]
    category_counts = [item['count'] for item in category_data]

    nonmed_category_data = NonMedicalProduct.objects.values('category').annotate(count=Count('id')).order_by('-count')
    nonmed_category_labels = [item['category'] for item in nonmed_category_data]
    nonmed_category_counts = [item['count'] for item in nonmed_category_data]

    recent_medicines = Medicine.objects.all().order_by('-manufacture_date')[:5]

    all_actions = MedicineAction.objects.all().order_by('-timestamp')
    paginator = Paginator(all_actions, 10)
    page = request.GET.get('page', 1)
    try:
        recent_actions = paginator.page(page)
    except PageNotAnInteger:
        recent_actions = paginator.page(1)
    except EmptyPage:
        recent_actions = paginator.page(paginator.num_pages)

    context = {
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'near_expiry_count': near_expiry_count,
        'expired_count': expired_count,
        'total_nonmedical': total_nonmedical,
        'nonmedical_low_stock_count': nonmedical_low_stock_count,
        'nonmedical_active_count': nonmedical_active_count,
        'nonmedical_categories_count': nonmedical_categories_count,
        'category_labels': category_labels,
        'category_counts': category_counts,
        'nonmed_category_labels': nonmed_category_labels,
        'nonmed_category_counts': nonmed_category_counts,
        'recent_medicines': recent_medicines,
        'recent_actions': recent_actions,
        # Add online orders data
        'pending_orders_count': pending_orders_count,
        'processing_orders_count': processing_orders_count,
        'total_orders_today': total_orders_today,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
    }
    return render(request, 'Medicine_inventory/med_inventory_dash.html', context)


# -------------------- Utility Views --------------------

@pharmacist_required
def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    recent_actions = MedicineAction.objects.filter(medicine=medicine).order_by('-timestamp')[:15]
    profit = None
    margin_pct = None
    try:
        if medicine.cost_price is not None and medicine.selling_price is not None:
            profit = medicine.selling_price - medicine.cost_price
            if medicine.cost_price and medicine.cost_price > 0:
                margin_pct = (profit / medicine.cost_price) * Decimal('100')
    except (InvalidOperation, ZeroDivisionError):
        profit = None
        margin_pct = None
    context = {
        'medicine': medicine,
        'recent_actions': recent_actions,
        'profit': profit,
        'margin_pct': margin_pct,
    }
    return render(request, 'Medicine_inventory/medicine_detail.html', context)


@pharmacist_required
def medicine_list(request):
    category = request.GET.get('category')
    sort_by = request.GET.get('sort')

    if category:
        request.session['medicine_category_filter'] = category
    if sort_by:
        request.session['medicine_sort_by'] = sort_by

    if not category and 'medicine_category_filter' in request.session:
        category = request.session['medicine_category_filter']
    if not sort_by and 'medicine_sort_by' in request.session:
        sort_by = request.session['medicine_sort_by']

    medicines = Medicine.objects.all()
    if category and category != 'all':
        medicines = medicines.filter(category=category)

    if sort_by == 'name':
        medicines = medicines.order_by('name')
    elif sort_by == 'price_low':
        medicines = medicines.order_by('price')

    context = {
        'medicines': medicines,
        'current_category': category,
        'current_sort': sort_by,
    }
    return render(request, 'Medicine_inventory/medicine_list.html', context)


@pharmacist_required
def clear_filters(request):
    request.session.pop('medicine_category_filter', None)
    request.session.pop('medicine_sort_by', None)
    return redirect('medicine_list')



@pharmacist_required
def medicine_detail(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    cost = medicine.cost_price or 0
    sell = medicine.selling_price or 0
    profit = sell - cost if cost and sell else None
    profit_percent = (profit / cost * 100) if profit is not None and cost > 0 else None
    context = {
        'medicine': medicine,
        'profit': profit,
        'profit_percent': profit_percent
    }
    return render(request, 'Medicine_inventory/medicine_detail.html', context)


@pharmacist_required
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine updated.")
            return redirect('medicine_detail', pk=medicine.pk)
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'Medicine_inventory/medicine_form.html', {'form': form, 'medicine': medicine})


@pharmacist_required
def view_online_orders(request):
    """View and manage online orders"""
    try:
        from onlineStore.models import Order
    except ImportError:
        messages.error(request, "Order management is not available.")
        return redirect('med_inventory_dash')
    
    # Use select_related to fetch customer data efficiently
    orders = Order.objects.select_related('customer_user').all().order_by('-created_at')
    
    # Calculate statistics
    total_orders = orders.count()
    pending_orders = orders.filter(status='Pending').count()
    processing_orders = orders.filter(status='Processing').count()
    completed_orders = orders.filter(status='Completed').count()
    cancelled_orders = orders.filter(status='Cancelled').count()
    delivered_orders = orders.filter(status='Delivered').count()
    
    # Search functionality - enhanced to include customer fields
    search_query = request.GET.get('search', '').strip()
    
    # Fix: Check for actual content, not just if the parameter exists
    if search_query and search_query.lower() not in ['', 'none', 'null']:
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(customer_user__first_name__icontains=search_query) |
            Q(customer_user__last_name__icontains=search_query) |
            Q(customer_user__email__icontains=search_query) |
            Q(customer_user__phone__icontains=search_query) |
            Q(shipping_address__icontains=search_query)
        )
    
    # Apply status filter
    status_filter = request.GET.get('status')
    if status_filter and status_filter.lower() not in ['', 'none', 'null']:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 15)
    page = request.GET.get('page', 1)
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    # Clean up search query for template (remove 'None' strings)
    if search_query and search_query.lower() in ['none', 'null']:
        search_query = ''
    
    context = {
        'orders': orders,
        'current_status': status_filter,
        'search_query': search_query,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'delivered_orders': delivered_orders,
    }
    return render(request, 'Medicine_inventory/onlineStoreOrder.html', context)


@pharmacist_required
def order_detail(request, order_id):
    """Display detailed view of an order with complete customer information"""
    try:
        from onlineStore.models import Order
    except ImportError:
        messages.error(request, "Order management is not available.")
        return redirect('med_inventory_dash')
    
    # Use select_related to fetch customer and order items data efficiently
    order = get_object_or_404(
        Order.objects.select_related('customer_user'), 
        order_id=order_id
    )
    order_items = order.items.all().select_related('product')
    
    # Calculate totals for each item
    for item in order_items:
        item.total_price = item.quantity * item.price
    
    # Get customer information
    customer = order.customer_user
    
    context = {
        'order': order,
        'order_items': order_items,
        'customer': customer,
    }
    return render(request, 'Medicine_inventory/order_detail.html', context)


@pharmacist_required
def update_order_status(request, order_id):
    """Update the status of an order"""
    try:
        from onlineStore.models import Order
    except ImportError:
        messages.error(request, "Order management is not available.")
        return redirect('med_inventory_dash')
    
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id)
        new_status = request.POST.get('status')
        old_status = order.status
        
        # Define valid status choices - make sure these match your model
        VALID_STATUSES = [
            'Pending',
            'Payment_Failed', 
            'Paid',
            'Processing',
            'Shipped',
            'Delivered',
            'Cancelled'
        ]
        
        if new_status in VALID_STATUSES:
            # Handle inventory restoration for cancelled orders
            if new_status == 'Cancelled' and old_status != 'Cancelled':
                try:
                    # Get all order items
                    order_items = order.items.all().select_related('product')
                    
                    # Restore inventory for each item
                    restored_items = []
                    not_found_items = []
                    
                    for item in order_items:
                        item_restored = False
                        
                        # Try to restore from Medicine inventory first (by ID)
                        try:
                            medicine = Medicine.objects.get(id=item.product.id)
                            
                            # Restore the quantity
                            old_quantity = medicine.quantity_in_stock
                            medicine.quantity_in_stock += item.quantity
                            medicine.save()
                            
                            # Log the action for medicine
                            MedicineAction.objects.create(
                                medicine=medicine,
                                medicine_name=medicine.name,
                                batch_number=medicine.batch_number,
                                action='Updated',
                                user=request.user,
                                details=f'Restored stock (Order #{order_id} cancelled) - Quantity: {item.quantity} units. Stock: {old_quantity} → {medicine.quantity_in_stock}'
                            )
                            
                            restored_items.append({
                                'name': medicine.name,
                                'quantity': item.quantity,
                                'new_stock': medicine.quantity_in_stock,
                                'type': 'Medicine'
                            })
                            
                            item_restored = True
                            
                        except Medicine.DoesNotExist:
                            # Try to restore from Non-Medicine inventory (by ID)
                            try:
                                non_medicine = NonMedicalProduct.objects.get(id=item.product.id)
                                
                                # Restore the quantity
                                old_quantity = non_medicine.stock
                                non_medicine.stock += item.quantity
                                non_medicine.save()
                                
                                # Log the action for non-medicine
                                MedicineAction.objects.create(
                                    medicine=None,  # No medicine reference
                                    medicine_name=non_medicine.name,
                                    batch_number=getattr(non_medicine, 'batch_number', 'N/A'),
                                    action='Updated',
                                    user=request.user,
                                    details=f'Restored non-medicine stock (Order #{order_id} cancelled) - Product: {non_medicine.name}, Quantity: {item.quantity} units. Stock: {old_quantity} → {non_medicine.stock}'
                                )
                                
                                restored_items.append({
                                    'name': non_medicine.name,
                                    'quantity': item.quantity,
                                    'new_stock': non_medicine.stock,
                                    'type': 'Non-Medicine'
                                })
                                
                                item_restored = True
                                
                            except NonMedicalProduct.DoesNotExist:
                                # ID not found in either inventory, try by name
                                pass
                        
                        # If not found by ID, try by name (only if not already restored)
                        if not item_restored:
                            # Try medicine by name first
                            try:
                                medicine = Medicine.objects.get(name=item.product.name)
                                old_quantity = medicine.quantity_in_stock
                                medicine.quantity_in_stock += item.quantity
                                medicine.save()
                                
                                MedicineAction.objects.create(
                                    medicine=medicine,
                                    medicine_name=medicine.name,
                                    batch_number=medicine.batch_number,
                                    action='Updated',
                                    user=request.user,
                                    details=f'Restored stock by name match (Order #{order_id} cancelled) - Quantity: {item.quantity} units. Stock: {old_quantity} → {medicine.quantity_in_stock}'
                                )
                                
                                restored_items.append({
                                    'name': medicine.name,
                                    'quantity': item.quantity,
                                    'new_stock': medicine.quantity_in_stock,
                                    'type': 'Medicine'
                                })
                                
                                item_restored = True
                                
                            except Medicine.DoesNotExist:
                                # Try non-medicine by name
                                try:
                                    non_medicine = NonMedicalProduct.objects.get(name=item.product.name)
                                    old_quantity = non_medicine.stock
                                    non_medicine.stock += item.quantity
                                    non_medicine.save()
                                    
                                    MedicineAction.objects.create(
                                        medicine=None,
                                        medicine_name=non_medicine.name,
                                        batch_number=getattr(non_medicine, 'batch_number', 'N/A'),
                                        action='Updated',
                                        user=request.user,
                                        details=f'Restored non-medicine stock by name match (Order #{order_id} cancelled) - Product: {non_medicine.name}, Quantity: {item.quantity} units. Stock: {old_quantity} → {non_medicine.stock}'
                                    )
                                    
                                    restored_items.append({
                                        'name': non_medicine.name,
                                        'quantity': item.quantity,
                                        'new_stock': non_medicine.stock,
                                        'type': 'Non-Medicine'
                                    })
                                    
                                    item_restored = True
                                    
                                except NonMedicalProduct.DoesNotExist:
                                    # Item not found anywhere
                                    not_found_items.append({
                                        'name': item.product.name,
                                        'quantity': item.quantity
                                    })
                    
                    # Update order status
                    order.status = new_status
                    order.save()
                    
                    # Create success message with details
                    success_messages = []
                    
                    if restored_items:
                        medicine_items = [item for item in restored_items if item['type'] == 'Medicine']
                        non_medicine_items = [item for item in restored_items if item['type'] == 'Non-Medicine']
                        
                        if medicine_items:
                            medicine_details = ", ".join([
                                f"{item['name']} (+{item['quantity']} units)" 
                                for item in medicine_items
                            ])
                            success_messages.append(f"Medicine inventory restored: {medicine_details}")
                        
                        if non_medicine_items:
                            non_medicine_details = ", ".join([
                                f"{item['name']} (+{item['quantity']} units)" 
                                for item in non_medicine_items
                            ])
                            success_messages.append(f"Non-medicine inventory restored: {non_medicine_details}")
                    
                    if not_found_items:
                        not_found_details = ", ".join([
                            f"{item['name']} ({item['quantity']} units)" 
                            for item in not_found_items
                        ])
                        messages.warning(
                            request, 
                            f"Could not restore the following items (not found in any inventory): {not_found_details}"
                        )
                    
                    if success_messages:
                        messages.success(
                            request, 
                            f'Order {order_id} cancelled successfully. {" | ".join(success_messages)}'
                        )
                    else:
                        messages.success(
                            request, 
                            f'Order {order_id} cancelled successfully. No inventory items to restore.'
                        )
                        
                except Exception as e:
                    messages.error(
                        request, 
                        f'Error processing cancellation: {str(e)}. Order status not updated.'
                    )
                    return redirect('order_detail', order_id=order_id)
                    
            else:
                # Normal status update (not cancellation)
                order.status = new_status
                order.save()
                
                messages.success(
                    request, 
                    f'Order {order_id} status updated from "{old_status}" to "{new_status}" successfully.'
                )
        else:
            messages.error(request, f'Invalid status selected: "{new_status}". Please select a valid status.')
            
        return redirect('order_detail', order_id=order_id)
    
    return redirect('view_online_orders')

import csv
from django import forms

class BulkUploadForm(forms.Form):
    csv_file = forms.FileField(label="CSV File")

@pharmacist_required
def bulk_upload_medicines(request):
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('medicine_table')
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            created_count = 0
            errors = []
            for idx, row in enumerate(reader, start=2):
                try:
                    supplier_name = row.get('supplier', '').strip()
                    supplier = None
                    if supplier_name:
                        supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
                    medicine = Medicine(
                        name=row.get('name', '').strip(),
                        category=row.get('category', '').strip(),
                        medicine_type=row.get('medicine_type', '').strip(),
                        dosage=row.get('dosage', '').strip(),
                        batch_number=row.get('batch_number', '').strip(),
                        manufacture_date=row.get('manufacturing_date', None) or None,
                        expiry_date=row.get('expiry_date', None) or None,
                        selling_price=row.get('selling_price', 0) or 0,
                        cost_price=row.get('cost_price', 0) or 0,
                        quantity_in_stock=row.get('quantity_in_stock', 0) or 0,
                        reorder_level=row.get('reorder_level', 0) or 0,
                        brand=row.get('brand', '').strip(),
                        supplier=supplier,
                        description=row.get('description', '').strip(),
                        # image_url=row.get('image_url', '').strip(),
                    )
                    medicine.full_clean()
                    medicine.save()
                    MedicineAction.objects.create(
                        medicine=medicine,
                        action='Bulk Uploaded',
                        user=request.user,
                        details='Bulk upload via CSV'
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
            if created_count:
                messages.success(request, f"Successfully uploaded {created_count} medicines.")
            if errors:
                messages.error(request, "Some rows could not be uploaded:<br>" + "<br>".join(errors))
            return redirect('medicine_table')
    return redirect('medicine_table')

@pharmacist_required
def bulk_upload_medicines(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'Please select a CSV file to upload.')
            return redirect('medicine_cards')
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(decoded_file))
            
            created_count = 0
            error_count = 0
            with_images_count = 0
            without_images_count = 0
            missing_images = []
            
            # Ensure the medical_products directory exists
            medical_products_path = ensure_medical_products_directory()
            
            for row_number, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is headers
                try:
                    # Handle image path from CSV
                    image_file = None
                    image_path = row.get('image_path', '').strip()
                    
                    # Only try to process image if image_path is provided and not empty
                    if image_path:
                        # Construct full path to image
                        full_image_path = os.path.join(medical_products_path, image_path)
                        
                        # Check if image file exists
                        if os.path.exists(full_image_path):
                            try:
                                # Read the image file
                                with open(full_image_path, 'rb') as img_file:
                                    image_content = img_file.read()
                                    # Create Django file object
                                    image_file = ContentFile(image_content, name=image_path)
                                    with_images_count += 1
                            except Exception as img_error:
                                print(f"Error reading image {image_path}: {img_error}")
                                missing_images.append(f"{row.get('name', 'Unknown')} (Row {row_number}): {image_path} - Read error")
                                without_images_count += 1
                        else:
                            missing_images.append(f"{row.get('name', 'Unknown')} (Row {row_number}): {image_path} - File not found")
                            without_images_count += 1
                    else:
                        # No image path provided - this is fine, medicine will be created without image
                        without_images_count += 1
                    
                    # Handle supplier creation/lookup
                    supplier_name = row.get('supplier', '').strip()
                    supplier = None
                    if supplier_name:
                        try:
                            supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
                        except Exception as supplier_error:
                            print(f"Error creating/getting supplier {supplier_name}: {supplier_error}")
                    
                    # Create medicine record (with or without image)
                    medicine = Medicine.objects.create(
                        name=row.get('name', '').strip(),
                        category=row.get('category', '').strip(),
                        medicine_type=row.get('medicine_type', '').strip(),
                        dosage=row.get('dosage', '').strip(),
                        batch_number=row.get('batch_number', '').strip(),
                        manufacture_date=datetime.strptime(row.get('manufacturing_date', ''), '%Y-%m-%d').date() if row.get('manufacturing_date', '').strip() else None,
                        expiry_date=datetime.strptime(row.get('expiry_date', ''), '%Y-%m-%d').date() if row.get('expiry_date', '').strip() else None,
                        selling_price=Decimal(row.get('selling_price', '0') or '0'),
                        cost_price=Decimal(row.get('cost_price', '0') or '0'),
                        quantity_in_stock=int(row.get('quantity_in_stock', '0') or '0'),
                        reorder_level=int(row.get('reorder_level', '0') or '0'),
                        brand=row.get('brand', '').strip(),
                        supplier=supplier,
                        description=row.get('description', '').strip(),
                        image=image_file,  # This will be None if no image, which is perfectly fine
                        # created_by=request.user
                        available_online=row.get('available_online', '').strip().upper() == 'FALSE'
                    )
                    
                    # Log the action
                    MedicineAction.objects.create(
                        medicine=medicine,
                        action='Bulk Uploaded',
                        user=request.user,
                        details=f'Bulk upload via CSV - {"With image" if image_file else "Without image"}'
                    )
                    
                    created_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row {row_number}: {e}")
                    # Add the row data to error message for debugging
                    missing_images.append(f"Row {row_number} ({row.get('name', 'Unknown')}): Processing error - {str(e)}")
            
            # Build comprehensive success message
            success_parts = []
            if created_count > 0:
                success_parts.append(f"Successfully uploaded {created_count} medicines")
                
                # Add image statistics
                if with_images_count > 0 and without_images_count > 0:
                    success_parts.append(f"({with_images_count} with images, {without_images_count} without images)")
                elif with_images_count > 0:
                    success_parts.append(f"({with_images_count} with images)")
                elif without_images_count > 0:
                    success_parts.append(f"({without_images_count} without images - will show default 'no image' placeholder)")
            
            if success_parts:
                messages.success(request, ' '.join(success_parts) + '!')
            
            # Handle warnings for missing images (but not errors since medicines were still created)
            image_warnings = [msg for msg in missing_images if "File not found" in msg or "Read error" in msg]
            processing_errors = [msg for msg in missing_images if "Processing error" in msg]
            
            if image_warnings:
                warning_msg = f"Note: {len(image_warnings)} image(s) could not be loaded (medicines created without images):\n"
                warning_msg += '\n'.join(image_warnings[:3])  # Show first 3
                if len(image_warnings) > 3:
                    warning_msg += f"\n... and {len(image_warnings) - 3} more"
                messages.warning(request, warning_msg)
            
            # Handle actual processing errors
            if error_count > 0:
                error_msg = f'{error_count} medicines could not be processed due to data errors'
                if processing_errors:
                    error_msg += ":\n" + '\n'.join(processing_errors[:3])
                    if len(processing_errors) > 3:
                        error_msg += f"\n... and {len(processing_errors) - 3} more"
                messages.error(request, error_msg)
                
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
        
        return redirect('medicine_cards')
    
    return redirect('medicine_cards')

# Add this function to create the directory if it doesn't exist:

def ensure_medical_products_directory():
    """Ensure the medical_products directory exists in media folder"""
    medical_products_path = os.path.join(settings.MEDIA_ROOT, 'medical_products')
    if not os.path.exists(medical_products_path):
        os.makedirs(medical_products_path, exist_ok=True)
    return medical_products_path

# Add this helper view:

@pharmacist_required
def show_media_path(request):
    """Show the media path for users to know where to place images"""
    medical_products_path = ensure_medical_products_directory()
    
    context = {
        'media_path': medical_products_path,
        'relative_path': 'media/medical_products/',
        'example_files': [
            'paracetamol.jpg',
            'amoxicillin.png', 
            'vitamin_c.jpg'
        ]
    }
    
    messages.info(request, f'''
    <strong>Image Upload Directory:</strong><br>
    Place your medicine images in: <code>{medical_products_path}</code><br><br>
    <strong>In your CSV, use just the filename:</strong><br>
    • paracetamol.jpg<br>
    • amoxicillin.png<br>
    • vitamin_c.jpg
    ''')
    
    return redirect('medicine_cards')

@pharmacist_required
def toggle_medicine_online(request, pk):
    """Toggle the available_online status for a medicine"""
    if request.method == 'POST':
        medicine = get_object_or_404(Medicine, pk=pk)
        
        # Toggle the available_online field
        medicine.available_online = not medicine.available_online
        medicine.save()
        
        status = "enabled" if medicine.available_online else "disabled"
        messages.success(request, f'Online availability for "{medicine.name}" has been {status}.')
        
        # Redirect back to the previous page
        return redirect(request.META.get('HTTP_REFERER', 'medicine_cards'))
    
    return redirect('medicine_cards')