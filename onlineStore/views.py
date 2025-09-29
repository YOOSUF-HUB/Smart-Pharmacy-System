from multiprocessing import context
from django.shortcuts import get_object_or_404, render, redirect
from .models import Cart, Order, Product, CartItem, OrderItem
from django.db.models import Q
from django.db.models.functions import Coalesce

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

from Medicine_inventory.models import Medicine
from Non_Medicine_inventory.models import NonMedicalProduct


#payments
import stripe
from django.conf import settings
from django.http import JsonResponse
import json
# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# Customer required
def customer_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "customer")(view_func)

def about_us(request):
    return render(request, 'onlineStore/about_us.html')


# Customer Order View
@customer_required
def order_history(request):
    orders = Order.objects.filter(customer_user=request.user).order_by('-created_at')
    return render(request, 'onlineStore/order_history.html', {'orders': orders})


# Homepage view
def online_store_homepage(request):
    featured_products = Product.objects.filter(
        featured=True, 
        available_online=True
    ).filter(
        Q(medicine__available_online=True) |  # Medicine must be available_online
        Q(non_medical_product__available_online=True)  # NonMedicalProduct must be available_online
    ).select_related('medicine', 'non_medical_product')[:6]
    
    context = {
        'featured_products': featured_products
    }
    return render(request, 'onlineStore/homepage.html', context)

def products(request):
    # Start with all available online products
    products = Product.objects.filter(
        available_online=True, product_type='NonMedicalProduct'
    ).select_related('medicine', 'non_medical_product')

    # Ensure related items are available online
    products = products.filter(
        Q(medicine__available_online=True) |
        Q(non_medical_product__available_online=True)
    )

    # Always exclude 'Medical Devices'
    products = products.exclude(
        Q(medicine__category='Medical Devices') |
        Q(non_medical_product__category='Medical Devices')
    )

    # Filters from GET params
    product_type = request.GET.get('type', '')
    category = request.GET.get('category', '').strip()
    search_query = request.GET.get('search', '').strip()

    if product_type:
        products = products.filter(product_type=product_type)

    if category:
        products = products.filter(
            Q(medicine__category=category) |
            Q(non_medical_product__category=category)
        )

    if search_query:
        products = products.filter(
            Q(medicine__name__icontains=search_query) |
            Q(medicine__brand__icontains=search_query) |
            Q(non_medical_product__name__icontains=search_query) |
            Q(non_medical_product__brand__icontains=search_query)
        )

    context = {
        'products': products,
        'medicine_categories': Medicine.CATEGORY_CHOICES,
        'non_medical_categories': NonMedicalProduct.CATEGORY_CHOICES,
        'current_type': product_type,
        'current_category': category,
        'search_query': search_query,
    }

    return render(request, 'onlineStore/products.html', context)




# Medicine Product listing view
def medicine_products(request):
    # Only show products that are available online AND their source inventory is available online
    products = Product.objects.filter(available_online=True, product_type='Medicine').select_related(
        'medicine', 'non_medical_product'
    )
    
    # Additional filter: ensure both Medicine and NonMedicalProduct items are also available_online
    products = products.filter(
        Q(medicine__available_online=True) |  # Medicine must be available_online
        Q(non_medical_product__available_online=True)  # NonMedicalProduct must be available_online
    )
    
    product_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    search_query = request.GET.get('search', '').strip()
    
    if product_type:
        products = products.filter(product_type=product_type)
    
    if category:
        # Filter across both related models using Q objects
        products = products.filter(
            Q(medicine__category=category) | 
            Q(non_medical_product__category=category)
        )
    
    if search_query:
        products = products.filter(
            Q(medicine__name__icontains=search_query) |
            Q(medicine__brand__icontains=search_query) |
            Q(non_medical_product__name__icontains=search_query) |
            Q(non_medical_product__brand__icontains=search_query)
        )
    
    # Get categories for category filter dropdown
    medicine_categories = Medicine.CATEGORY_CHOICES
    non_medical_categories = NonMedicalProduct.CATEGORY_CHOICES
    
    context = {
        'products': products,
        'medicine_categories': medicine_categories,
        'non_medical_categories': non_medical_categories,
        'current_type': product_type,
        'current_category': category,
        'search_query': search_query,
    }
    
    return render(request, 'onlineStore/medicine_product.html', context)



from django.db.models import Q

from django.db.models import Q, F, Value
from django.db.models.functions import Coalesce


# Medical Devices View
def medical_devices_view(request):
    products = Product.objects.filter(available_online=True, product_type='NonMedicalProduct').select_related(
        'medicine', 'non_medical_product'
    )
    
    # Ensure related items are available online
    products = products.filter(
        Q(medicine__available_online=True) |
        Q(non_medical_product__available_online=True)
    )

    product_type = request.GET.get('type', '')
    category = request.GET.get('category', 'Medical Devices')
    search_query = request.GET.get('search', '').strip()

    # Annotate price using Coalesce (use medicine.selling_price if exists, else non_medical_product.selling_price)
    from django.db.models import FloatField
    products = products.annotate(
        effective_price=Coalesce(
            F('medicine__selling_price'),
            F('non_medical_product__selling_price'),
            output_field=FloatField()
        )
    )

    # Price filter (validate and apply only when provided)
    min_price = request.GET.get('min_price', '0').strip()
    max_price = request.GET.get('max_price', '100000').strip()

    try:
        if min_price != '0':
            products = products.filter(effective_price__gte=float(min_price))
        if max_price != '100000':
            products = products.filter(effective_price__lte=float(max_price))
    except ValueError:
        # ignore invalid numeric inputs (or add messages.error as needed)
        pass

    if product_type:
        products = products.filter(product_type=product_type)

    if category:
        products = products.filter(
            Q(medicine__category=category) |
            Q(non_medical_product__category=category)
        )

    if search_query:
        products = products.filter(
            Q(medicine__name__icontains=search_query) |
            Q(medicine__brand__icontains=search_query) |
            Q(non_medical_product__name__icontains=search_query) |
            Q(non_medical_product__brand__icontains=search_query)
        )

    medicine_categories = Medicine.CATEGORY_CHOICES
    non_medical_categories = NonMedicalProduct.CATEGORY_CHOICES

    context = {
        'products': products,
        'medicine_categories': medicine_categories,
        'non_medical_categories': non_medical_categories,
        'current_type': product_type,
        'current_category': category,
        'search_query': search_query,
        'current_min_price': min_price,
        'current_max_price': max_price,
    }

    return render(request, 'onlineStore/medical_device.html', context)



# Product detail view 
def product_detail(request, pk):
    # First get the product
    product = get_object_or_404(
        Product.objects.select_related('medicine', 'non_medical_product'), 
        pk=pk, 
        available_online=True
    )
    
    # Additional check: ensure the source inventory item is available online
    if product.medicine and not product.medicine.available_online:
        messages.error(request, "This medicine is currently not available online.")
        return redirect('onlineStore:products')
    elif product.non_medical_product and not product.non_medical_product.available_online:
        messages.error(request, "This product is currently not available online.")
        return redirect('onlineStore:products')
    
    related_products = []
    inventory_item = product.medicine or product.non_medical_product

    if inventory_item:
        product_type_field_name = 'medicine' if product.product_type == 'Medicine' else 'non_medical_product'

        related_products = Product.objects.filter(
            available_online=True,
            product_type=product.product_type,
            **{f'{product_type_field_name}__category': inventory_item.category}
        ).filter(
            Q(medicine__available_online=True) |  # Medicine must be available_online
            Q(non_medical_product__available_online=True)  # NonMedicalProduct must be available_online
        ).exclude(pk=pk)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    
    return render(request, 'onlineStore/productDetail.html', context)



@customer_required
def add_to_cart(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk, available_online=True)
        
        # Additional check for both Medicine and NonMedicalProduct
        if product.medicine and not product.medicine.available_online:
            messages.error(request, "This medicine is not available for online purchase.")
            return redirect('onlineStore:products')
        elif product.non_medical_product and not product.non_medical_product.available_online:
            messages.error(request, "This product is not available for online purchase.")
            return redirect('onlineStore:products')
        
        quantity = int(request.POST.get('quantity'))
        
        if quantity <= 0:
            messages.error(request, "Invalid quantity")
            return redirect('onlineStore:product_detail', pk=pk)
        
        if quantity > product.stock:
            messages.error(request, f"Only {product.stock} items available in stock")
            return redirect('onlineStore:product_detail', pk=pk)
        
        # create cart 
        cart, created = Cart.objects.get_or_create(customer_user=request.user)
        
        # create cart item
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not item_created:
            # if item already exists, update quantity
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                messages.error(request, f"Cannot add more. Only {product.stock} items available")
                return redirect('onlineStore:product_detail', pk=pk)
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f"Updated {product.name} quantity to {cart_item.quantity}")
        else:
            messages.success(request, f"Added {product.name} to cart")
        
        return redirect('onlineStore:cart')
    
    return redirect('onlineStore:product_detail', pk=pk)

@customer_required
def cart_view(request):
    try:
        cart = Cart.objects.get(customer_user=request.user)  
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart = None
        cart_items = []
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total': cart.total_price if cart else 0,
    }
    
    return render(request, 'onlineStore/cart.html', context)

@customer_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer_user=request.user)  # Changed to customer_user
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, f"Removed {cart_item.product.name} from cart")
        elif quantity > cart_item.product.stock:
            messages.error(request, f"Only {cart_item.product.stock} items available")
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f"Updated {cart_item.product.name} quantity")
    
    return redirect('onlineStore:cart')

@customer_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__customer_user=request.user)  # Changed to customer_user
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"Removed {product_name} from cart")
    return redirect('onlineStore:cart')



# ...existing code...

from accounts.models import Customer

@customer_required
def checkout_view(request):
    try:
        cart = Cart.objects.get(customer_user=request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty")
        return redirect('onlineStore:cart')
    
    # Check if cart is empty
    if not cart_items:
        messages.error(request, "Your cart is empty")
        return redirect('onlineStore:cart')
    
    # Get or create customer profile
    customer, created = Customer.objects.get_or_create(user=request.user)
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        return process_checkout(request, cart, cart_items, customer)
    
    # Show checkout form (GET request)
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total': cart.total_price,
        'customer': customer,  # Pass customer data to pre-fill form
    }
    return render(request, 'onlineStore/checkout.html', context)

# Update your process_checkout function
# Remove the duplicate process_checkout function and keep only this one:

def process_checkout(request, cart, cart_items, customer):
    """Process the checkout form submission"""
    
    # Extract form data from POST request
    first_name = request.POST.get('first-name', '').strip()
    last_name = request.POST.get('last-name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()
    city = request.POST.get('city', '').strip()
    postal_code = request.POST.get('postal-code', '').strip()
    country = request.POST.get('country', '').strip()
    update_profile = request.POST.get('update_profile', False)
    
    # Validation code
    if not all([first_name, last_name, email, address, city]):
        messages.error(request, "Please fill in all required fields")
        return redirect('onlineStore:checkout')
    
    if '@' not in email:
        messages.error(request, "Please enter a valid email address")
        return redirect('onlineStore:checkout')
    
    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(request, f"Sorry, only {item.product.stock} units of {item.product.name} available")
            return redirect('onlineStore:cart')
    
    try:
        # Update customer profile if requested
        if update_profile:
            customer.phone = phone
            customer.address = address
            customer.city = city
            customer.save()
            
            # Update user info too
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.save()
        
        # Create Order FIRST (before payment)
        order = Order.objects.create(
            customer_user=request.user,
            total_amount=cart.total_price,
            status='Pending',
            payment_status='pending',
            shipping_first_name=first_name,
            shipping_last_name=last_name,
            shipping_email=email,
            shipping_phone=phone,
            shipping_address=address,
            shipping_city=city,
            shipping_postal_code=postal_code,
            shipping_country=country,
        )
        
        # Create OrderItems (before payment)
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # REDIRECT TO PAYMENT PAGE instead of completing order
        return redirect('onlineStore:payment', order_id=order.order_id)
        
    except Exception as e:
        messages.error(request, f"There was an error processing your order: {str(e)}")
        return redirect('onlineStore:checkout')

@customer_required
def payment_view(request, order_id):
    """Display payment page with Stripe integration"""
    order = get_object_or_404(Order, order_id=order_id, customer_user=request.user, status='Pending')
    
    try:
        # Create Stripe PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(order.total_amount * 100),  # Stripe uses cents
            currency='usd',  # Sri Lankan Rupee
            metadata={
                'order_id': order.order_id,
                'customer_email': order.shipping_email,
            }
        )
        
        # Save the payment intent ID
        order.stripe_payment_intent_id = intent.id
        order.save()
        
        context = {
            'order': order,
            'client_secret': intent.client_secret,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        }
        
        return render(request, 'onlineStore/payment.html', context)
        
    except Exception as e:
        messages.error(request, f"Payment setup failed: {str(e)}")
        return redirect('onlineStore:checkout')


@customer_required
def payment_success(request, order_id):
    """Handle successful payment"""
    order = get_object_or_404(Order, order_id=order_id, customer_user=request.user)
    
    try:
        # Verify payment with Stripe
        if order.stripe_payment_intent_id:
            intent = stripe.PaymentIntent.retrieve(order.stripe_payment_intent_id)
            
            if intent.status == 'succeeded':
                # Payment successful - complete the order
                order.status = 'Paid'
                order.payment_status = 'succeeded'
                order.save()
                
                # Now update inventory
                cart = Cart.objects.get(customer_user=request.user)
                for order_item in order.items.all():
                    if order_item.product.product_type == 'Medicine':
                        medicine = order_item.product.medicine
                        medicine.quantity_in_stock -= order_item.quantity
                        medicine.save()
                    elif order_item.product.product_type == 'NonMedicalProduct':
                        non_medical = order_item.product.non_medical_product
                        non_medical.stock -= order_item.quantity
                        non_medical.save()
                
                # Clear cart
                cart.items.all().delete()
                
                messages.success(request, f"Payment successful! Order #{order.order_id} confirmed.")
                return redirect('onlineStore:order_confirmation', order_id=order.order_id)
            else:
                order.payment_status = 'failed'
                order.status = 'Payment_Failed'
                order.save()
                messages.error(request, "Payment was not completed. Please try again.")
                return redirect('onlineStore:payment', order_id=order.order_id)
                
    except Exception as e:
        messages.error(request, f"Payment verification failed: {str(e)}")
        return redirect('onlineStore:payment', order_id=order.order_id)


@customer_required 
def payment_cancel(request, order_id):
    """Handle cancelled payment"""
    order = get_object_or_404(Order, order_id=order_id, customer_user=request.user)
    order.status = 'Payment_Failed'
    order.payment_status = 'cancelled'
    order.save()
    
    messages.warning(request, "Payment was cancelled. You can try again.")
    return redirect('onlineStore:cart')

@customer_required
def order_confirmation(request, order_id):
    """Display order confirmation page"""
    order = get_object_or_404(Order, order_id=order_id, customer_user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'onlineStore/orderConfirmation.html', context)

# ...existing code...









































# from django.shortcuts import get_object_or_404, render
# from .models import Product
# from django.db import models


# # Homepage view
# def online_store_homepage(request):
#     """
#     Display the online store homepage with featured products
#     """
#     # Get featured products for homepage display
#     featured_products = Product.objects.filter(
#         featured=True, 
#         available_online=True
#     )[:6]  # Limit to 6 featured products
    
#     context = {
#         'featured_products': featured_products
#     }
#     return render(request, 'onlineStore/homepage.html', context)


# # Product listing view
# def products(request):
#     """
#     Display all products with filtering options
#     """
#     # Get all available online products
#     products = Product.objects.filter(available_online=True)
    
#     # Get filter parameters from request
#     product_type = request.GET.get('type')  # 'medicine' or 'non_medical'
#     category = request.GET.get('category')
#     search_query = request.GET.get('search', '').strip()
#     sort_by = request.GET.get('sort', 'name')  # default sort by name
    
#     # Apply filters
#     if product_type:
#         products = products.filter(product_type=product_type)
    
#     # Filter by category (requires checking the linked model)
#     if category:
#         if product_type == 'medicine':
#             products = products.filter(medicine__category=category)
#         elif product_type == 'non_medical':
#             products = products.filter(non_medical_product__category=category)
    
#     # Search functionality
#     if search_query:
#         # Search in both medicine and non-medical product names
#         products = products.filter(
#             models.Q(medicine__name__icontains=search_query) |
#             models.Q(medicine__brand__icontains=search_query) |
#             models.Q(non_medical_product__name__icontains=search_query) |
#             models.Q(non_medical_product__brand__icontains=search_query)
#         )
    
#     # Sorting
#     if sort_by == 'price_low':
#         # Custom sorting since price is in related models
#         products = sorted(products, key=lambda p: p.get_price())
#     elif sort_by == 'price_high':
#         products = sorted(products, key=lambda p: p.get_price(), reverse=True)
#     elif sort_by == 'name':
#         products = sorted(products, key=lambda p: p.get_name())
    
#     # Get categories for filter dropdown
#     medicine_categories = []
#     non_medical_categories = []
    
#     if not product_type or product_type == 'medicine':
#         # Get unique medicine categories
#         from Medicine_inventory.models import Medicine
#         medicine_categories = Medicine.CATEGORY_CHOICES
    
#     if not product_type or product_type == 'non_medical':
#         # Get unique non-medical categories
#         from Non_Medicine_inventory.models import NonMedicalProduct
#         non_medical_categories = NonMedicalProduct.CATEGORY_CHOICES
    
#     context = {
#         'products': products,
#         'medicine_categories': medicine_categories,
#         'non_medical_categories': non_medical_categories,
#         'current_type': product_type,
#         'current_category': category,
#         'search_query': search_query,
#         'current_sort': sort_by,
#     }
    
#     return render(request, 'onlineStore/products.html', context)


# # Product detail view
# def product_detail(request, pk):
#     """
#     Display detailed information about a specific product
#     """
#     product = get_object_or_404(Product, pk=pk, available_online=True)
    
#     # Get related products (same category)
#     related_products = Product.objects.filter(
#         available_online=True,
#         product_type=product.product_type
#     ).exclude(pk=pk)[:4]  # Show 4 related products
    
#     # Additional product information based on type
#     additional_info = {}
#     if product.medicine:
#         additional_info = {
#             'dosage': product.medicine.dosage,
#             'category': product.medicine.category,
#             'medicine_type': product.medicine.medicine_type,
#             'description': product.medicine.description,
#             'requires_prescription': product.medicine.medicine_type == 'RX',
#         }
#     elif product.non_medical_product:
#         additional_info = {
#             'category': product.non_medical_product.category,
#             'description': product.non_medical_product.description,
#         }
    
#     context = {
#         'product': product,
#         'related_products': related_products,
#         'additional_info': additional_info,
#     }
    
#     return render(request, 'onlineStore/product_detail.html', context)


# onlineStore/views.py