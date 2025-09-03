# onlineStore/urls.py

from django.urls import include,path
from . import views

app_name = 'onlineStore' 

urlpatterns = [
    path('', views.online_store_homepage, name='homepage'),
    path('accounts/', include('accounts.urls')), # Include accounts URLs for login/logout
    path('products/', views.products, name='products'),
    
    # FIX: Corrected view name from `view_product_detail` to `product_detail`
    # FIX: Changed URL parameter from `<int:id>` to `<int:pk>` to match the view
    path('products/<int:pk>/', views.product_detail, name='product_detail'), 

    
    

    # Cart functionality
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Future: checkout functionality
    # path('checkout/', views.checkout, name='checkout'),
]