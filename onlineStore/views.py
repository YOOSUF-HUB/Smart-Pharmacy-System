from django.shortcuts import render

# Create your views here.
def online_store_homepage(request):
    return render(request, 'onlineStore/homepage.html')

def products(request):
    # This is a placeholder for the products view
    # You would typically fetch products from the database and pass them to the template
    return render(request, 'onlineStore/products.html', {'products': []})  # Replace with actual product data
