from django.shortcuts import render
from Medicine_inventory.models import Medicine

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

def checkout(request):
    return render(request, 'onlineStore/checkout.html')



def order_history(request):
    return render(request, 'onlineStore/orderHistory.html')