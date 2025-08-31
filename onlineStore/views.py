from django.shortcuts import get_object_or_404, redirect, render, HttpResponse
import Medicine_inventory
from Medicine_inventory.models import Medicine
from accounts.models import Customer
from .models import  Products

# Create your views here.
def online_store_homepage(request):
    return render(request, 'onlineStore/homepage.html')

# def products(request):
#     # This is a placeholder for the products view
#     # You would typically fetch products from the database and pass them to the template
#     return render(request, 'onlineStore/products.html', {'products': []})  # Replace with actual product data


# View all medicines
def products(request):
    # Get all medicines
    medicines = Medicine.objects.all()
    # categories = [c[0] for c in Medicine.CATEGORY_CHOICES]
    medTypes = [c[0] for c in Medicine.MEDICINE_TYPE_CHOICES]

    # Filtering
    category = request.GET.get('category')
    low_stock = request.GET.get('low_stock')

    if category:
        medicines = medicines.filter(category=category)
    filtered = []
    for med in medicines:
        med.low_stock = med.quantity_in_stock < med.reorder_level
        med.medicine_type = med.medicine_type if med.medicine_type in medTypes else 'Unknown'

        if low_stock == 'low' and not med.low_stock:
            continue
        filtered.append(med)
    return render(request, 'onlineStore/products.html', {'products': filtered})

def view_product_detail(request, id):
    try:
        product = Medicine.objects.get(id=id)
    except Medicine.DoesNotExist:
        product = None
    return render(request, 'onlineStore/productDetail.html', {'product': product})

# def checkout(request):
#     return render(request, 'onlineStore/checkout.html')



# def order_history(request):
#     return render(request, 'onlineStore/orderHistory.html')



# # Add to Cart
# def add_to_cart(request, product_id):
#     product = get_object_or_404(Products, id=product_id)  # ✅ use Products (model), not product (variable)
#     cart_item, created = Cart.objects.get_or_create(
#         product=product,
#         customer=request.user.customer  # make sure Customer has OneToOne with User
#     )
#     if not created:  # if already exists, increase qty
#         cart_item.quantity += 1
#         cart_item.save()
#     return redirect("view_cart")

# # View Cart
# def view_cart(request):
#     cart_items = Cart.objects.filter(customer=request.user.customer)
#     return render(request, "onlineStore/cart.html", {"cart_items": cart_items})

# # Checkout
# def checkout(request):
#     if request.method == "POST":
#         customer = request.user.customer
#         cart_items = Cart.objects.filter(customer=customer)

#         if not cart_items.exists():
#             return HttpResponse("Your cart is empty.")

#         order = Order.objects.create(customer=customer, status="In-Progress")

#         for item in cart_items:
#             order.Medicine.add(item.product)
#             item.delete()  # clear cart after order

#         return redirect("order_tracking", order_id=order.id)

#     return render(request, "onlineStore/checkout.html")