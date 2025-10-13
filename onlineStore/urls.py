# onlineStore/urls.py

from django.urls import include,path
from . import views

app_name = 'onlineStore' 

urlpatterns = [
    path('', views.online_store_homepage, name='homepage'),
    path('accounts/', include('accounts.urls')), # Include accounts URLs for login/logout
    path('products/', views.products, name='products'),
    path('products/medicine/', views.medicine_products, name='medicine-products'),
    path('products/medical-devices/', views.medical_devices_view, name='medical-devices'),
    
    # FIX: Corrected view name from `view_product_detail` to `product_detail`
    # FIX: Changed URL parameter from `<int:id>` to `<int:pk>` to match the view
    path('products/<int:pk>/', views.product_detail, name='product_detail'), 

    #About Us Page
    path('about/', views.about_us, name='about_us'),
    path('order-history/', views.order_history, name='order_history'),
    

    # Cart functionality
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # checkout functionality
    path('checkout/', views.checkout_view, name='checkout'),

    path('payment/<int:order_id>/', views.payment_view, name='payment'),
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('payment-cancel/<int:order_id>/', views.payment_cancel, name='payment_cancel'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
]