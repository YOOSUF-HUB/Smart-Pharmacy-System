from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import F
from .models import NonMedicalProduct
from .forms import NonMedicalProductForm
import csv
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings
import tempfile
import os
from django.utils import timezone
import base64
from django.contrib.auth.decorators import login_required
from io import StringIO
from decimal import Decimal
from datetime import datetime
from django.core.files.base import ContentFile


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import LoginView



import csv
import os
from io import StringIO
from decimal import Decimal
from datetime import datetime
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import user_passes_test


def pharmacist_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "pharmacist")(view_func)

@pharmacist_required
def product_list(request):
    """Display all non-medical products"""
    # Start with all products
    products = NonMedicalProduct.objects.all()
    
    # Get filter parameters from request
    category = request.GET.get('category')
    search_query = request.GET.get('search')
    
    # Apply filters
    if category:
        products = products.filter(category=category)
    
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Prepare context
    context = {
        'products': products,
        'categories': NonMedicalProduct.CATEGORY_CHOICES,
        'current_category': category,
        'search_query': search_query,
    }
    
    return render(request, 'Non_Medicine_inventory/product_list.html', context)

@pharmacist_required
def product_detail(request, slug):
    """Display details of a specific product"""
    product = get_object_or_404(NonMedicalProduct, slug=slug)
    context = {'product': product}
    return render(request, 'Non_Medicine_inventory/product_detail.html', context)

@pharmacist_required
def product_create(request):
    """Create a new non-medical product"""
    if request.method == 'POST':
        form = NonMedicalProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # Set default value if not provided
            # if not hasattr(product, 'available_online') or product.available_online is None:
            #     product.available_online = True
            product.save()
            messages.success(request, f'Product "{product.name}" has been created successfully.')
            return redirect('non_medicine:product_list')
    else:
        form = NonMedicalProductForm()
    
    context = {'form': form, 'title': 'Add New Product'}
    return render(request, 'Non_Medicine_inventory/product_form.html', context)

@pharmacist_required
def product_update(request, slug):
    """Update an existing non-medical product"""
    product = get_object_or_404(NonMedicalProduct, slug=slug)
    
    if request.method == 'POST':
        form = NonMedicalProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" has been updated successfully.')
            return redirect('non_medicine:product_detail', slug=product.slug)
    else:
        form = NonMedicalProductForm(instance=product)
    
    context = {'form': form, 'product': product, 'title': 'Update Product'}
    return render(request, 'Non_Medicine_inventory/product_form.html', context)

@pharmacist_required
def product_delete(request, slug):
    """Delete a non-medical product (supports AJAX confirmation modal)."""
    product = get_object_or_404(NonMedicalProduct, slug=slug)
    product_name = product.name

    # AJAX (modal) delete path
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.POST.get('confirm') == 'true':
            product.delete()
            messages.success(request, f'Product "{product_name}" has been deleted successfully.')
            # Return the current page URL for redirect
            redirect_url = request.META.get('HTTP_REFERER', '/non-medicine/table/')
            return JsonResponse({'status': 'ok', 'redirect': redirect_url})
        return JsonResponse({'status': 'cancelled'})

    # Standard (non-AJAX) POST (e.g. fallback form)
    if request.method == 'POST':
        if request.POST.get('confirm') == 'yes':
            product.delete()
            messages.success(request, f'Product "{product_name}" has been deleted successfully.')
            return redirect('non_medicine:product_list')
        messages.info(request, 'Deletion cancelled.')
        return redirect('non_medicine:product_detail', slug=product.slug)

    # GET never deletes – just return confirmation template (fallback)
    context = {'product': product}
    return render(request, 'Non_Medicine_inventory/product_confirm_delete.html', context)

@pharmacist_required
def product_table(request):
    """Display all non-medical products in a table format"""
    products = NonMedicalProduct.objects.all()
    
    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        products = products.filter(category=category)
    
    # Filter by search query if provided
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(name__icontains=search_query)
        
    # Get unique categories for filter dropdown
    categories = NonMedicalProduct.CATEGORY_CHOICES
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': category,
        'search_query': search_query,
    }
    return render(request, 'Non_Medicine_inventory/product_list_table.html', context)

@pharmacist_required
def export_pdf(request):
    # Get filtered products (same logic as in product_list view)
    products = NonMedicalProduct.objects.all()
    category = request.GET.get('category')
    search_query = request.GET.get('search')

    logo_file = os.path.join(settings.BASE_DIR, 'static/MediSyn_Logo/1.png')
    with open(logo_file, 'rb') as f:
        logo_data = base64.b64encode(f.read()).decode('utf-8')
    
    if category:
        products = products.filter(category=category)
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Prepare context for the template
    context = {
        'products': products,
        'title': 'Non-Medical Products Report',
        'now': timezone.now(),
        'logo_data': logo_data,
        'request': request,
    }
    
    # Render HTML content
    html_string = render_to_string('Non_Medicine_inventory/pdf_template.html', context)
    
    # Create HTTP response with PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="non_medical_products.pdf"'
    
    # Generate PDF from HTML
    HTML(string=html_string).write_pdf(response)
    
    return response

@pharmacist_required
def export_csv(request):
    # Get filtered products (same logic as in product_list view)
    products = NonMedicalProduct.objects.all()
    category = request.GET.get('category')
    search_query = request.GET.get('search')
    
    if category:
        products = products.filter(category=category)
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="non_medical_products.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Brand', 'Category', 'Description', 'Cost Price', 'Selling Price', 'Stock', 'Reorder Level', 'Status'])
    
    for product in products:
        writer.writerow([
            product.name,
            product.brand,
            product.get_category_display(),
            product.description,
            product.cost_price,
            product.selling_price,
            product.stock,
            product.reorder_level,
            'Active' if product.is_active else 'Inactive'
        ])
    
    return response

@pharmacist_required
def bulk_upload_products(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'Please select a CSV file to upload.')
            return redirect('non_medicine:product_table')
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(decoded_file))
            
            created_count = 0
            error_count = 0
            with_images_count = 0
            without_images_count = 0
            missing_images = []
            
            # Ensure the products directory exists
            products_path = ensure_products_directory()
            
            for row_number, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is headers
                try:
                    # Handle image path from CSV
                    image_file = None
                    image_path = row.get('image_path', '').strip()
                    
                    # Only try to process image if image_path is provided and not empty
                    if image_path:
                        # Construct full path to image
                        full_image_path = os.path.join(products_path, image_path)
                        
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
                        # No image path provided - this is fine, product will be created without image
                        without_images_count += 1
                    
                    # Create non-medical product record
                    product = NonMedicalProduct.objects.create(
                        name=row.get('name', '').strip(),
                        brand=row.get('brand', '').strip(),
                        category=row.get('category', '').strip(),
                        description=row.get('description', '').strip(),
                        cost_price=Decimal(row.get('cost_price', '0') or '0'),
                        selling_price=Decimal(row.get('selling_price', '0') or '0'),
                        stock=int(row.get('stock', '0') or '0'),
                        reorder_level=int(row.get('reorder_level', '0') or '0'),
                        available_online=row.get('available_online', '').strip().upper() in ['TRUE', '1', 'YES'],
                        image=image_file  # This will be None if no image, which is perfectly fine
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
                success_parts.append(f"Successfully uploaded {created_count} products")
                
                # Add image statistics
                if with_images_count > 0 and without_images_count > 0:
                    success_parts.append(f"({with_images_count} with images, {without_images_count} without images)")
                elif with_images_count > 0:
                    success_parts.append(f"({with_images_count} with images)")
                elif without_images_count > 0:
                    success_parts.append(f"({without_images_count} without images - will show default 'no image' placeholder)")
            
            if success_parts:
                messages.success(request, ' '.join(success_parts) + '!')
            
            # Handle warnings for missing images (but not errors since products were still created)
            image_warnings = [msg for msg in missing_images if "File not found" in msg or "Read error" in msg]
            processing_errors = [msg for msg in missing_images if "Processing error" in msg]
            
            if image_warnings:
                warning_msg = f"Note: {len(image_warnings)} image(s) could not be loaded (products created without images):\n"
                warning_msg += '\n'.join(image_warnings[:3])  # Show first 3
                if len(image_warnings) > 3:
                    warning_msg += f"\n... and {len(image_warnings) - 3} more"
                messages.warning(request, warning_msg)
            
            # Handle actual processing errors
            if error_count > 0:
                error_msg = f'{error_count} products could not be processed due to data errors'
                if processing_errors:
                    error_msg += ":\n" + '\n'.join(processing_errors[:3])
                    if len(processing_errors) > 3:
                        error_msg += f"\n... and {len(processing_errors) - 3} more"
                messages.error(request, error_msg)
                
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
        
        return redirect('non_medicine:product_table')
    
    return redirect('non_medicine:product_table')


def ensure_products_directory():
    """Ensure the products directory exists in media folder"""
    products_path = os.path.join(settings.MEDIA_ROOT, 'products')
    if not os.path.exists(products_path):
        os.makedirs(products_path, exist_ok=True)
    return products_path