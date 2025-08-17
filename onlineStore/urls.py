from django.urls import path
from . import views

urlpatterns = [
    path('', views.online_store_homepage, name='homepage'),  # Root now goes to homepage
    path('products/', views.products, name='products'),  # View all products
    # path('products/<int:id>/', views.view_product_detail, name='view_product_detail'), # View product detail by id
    # path('checkout/', views.checkout, name='checkout'), # Checkout page
    # path('cart/', views.view_cart, name='view_cart'),
    # path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    # path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    # path('cart/clear/', views.clear_cart, name='clear_cart'),
    # path('order/history/', views.order_history, name='order_history'),
    # path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    # path('search/', views.search_products, name='search_products'),
    # path('products/export/csv/', views.export_products_csv, name='export_products_csv'),
    # path('products/export/pdf/', views.export_products_pdf, name='export_products_pdf'),
]