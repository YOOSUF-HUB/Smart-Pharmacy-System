from django.urls import include, path
from . import views

app_name = 'onlineStore'  

urlpatterns = [
    path('', views.online_store_homepage, name='homepage'),  # Root now goes to homepage
    path('products/', views.products, name='products'),  # View all products
    path('products/<int:id>/', views.view_product_detail, name='productDetail'), # View product detail by id
    # path('checkout/', views.checkout, name='checkout'), # Checkout page
    # path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    # path('cart/', views.view_cart, name='view_cart'),
    
    # path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    # path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    # path('cart/clear/', views.clear_cart, name='clear_cart'),
    # path('order/history/', views.order_history, name='orderHistory'),
    # path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    # path('search/', views.search_products, name='search_products'),
    # path('products/export/csv/', views.export_products_csv, name='export_products_csv'),
    # path('products/export/pdf/', views.export_products_pdf, name='export_products_pdf'),


    # path('create-account/', views.create_account, name='create_account'),
    # path('login/', views.login, name='login'),
   path('customer/', include(('onlineCustomer_accounts.urls', 'onlineCustomer_accounts'), namespace='onlineCustomer_accounts')),  # Include customer account URLs

]