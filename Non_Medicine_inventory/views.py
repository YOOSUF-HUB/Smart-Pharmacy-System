from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import F
from .models import NonMedicalProduct
from .forms import NonMedicalProductForm


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

def product_detail(request, slug):
    """Display details of a specific product"""
    product = get_object_or_404(NonMedicalProduct, slug=slug)
    context = {'product': product}
    return render(request, 'Non_Medicine_inventory/product_detail.html', context)

def product_create(request):
    """Create a new non-medical product"""
    if request.method == 'POST':
        form = NonMedicalProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" has been created successfully.')
            return redirect('non_medicine:product_list')
    else:
        form = NonMedicalProductForm()
    
    context = {'form': form, 'title': 'Add New Product'}
    return render(request, 'Non_Medicine_inventory/product_form.html', context)

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

def product_delete(request, slug):
    """Delete a non-medical product"""
    product = get_object_or_404(NonMedicalProduct, slug=slug)
    product_name = product.name
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, f'Product "{product_name}" has been deleted successfully.')
        return redirect('non_medicine:product_list')
    
    context = {'product': product}
    return render(request, 'Non_Medicine_inventory/product_confirm_delete.html', context)

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