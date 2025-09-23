import base64
import csv
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, F, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from .forms import MedicineForm
from .models import Medicine, MedicineAction
from Non_Medicine_inventory.models import NonMedicalProduct



# Role check decorator
def pharmacist_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "pharmacist")(view_func)


# -------------------- Medicine Views --------------------

@pharmacist_required
def view_medicine(request):
    medicines = Medicine.objects.all()
    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

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


@pharmacist_required
def view_medicine_cards(request):
    medicines = Medicine.objects.all()
    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

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
        'recent_actions': recent_actions,
    })


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
    medicine_name = medicine.name

    MedicineAction.objects.create(
        medicine_name=medicine.name,
        batch_number=medicine.batch_number,
        action='Deleted',
        user=request.user
    )
    medicine.delete()

    messages.success(request, f"The record for '{medicine_name}' has been deleted successfully.")
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