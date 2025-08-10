from django.urls import path
from . import views


urlpatterns = [
    path('checkout/<int:pk>/', views.checkout_prescription, name='checkout_prescription'),
    path('success/<int:pk>/', views.success_payment, name='success_payment'),
    path('cancelled/<int:pk>/', views.cancel_payment, name='cancel_payment'),
    # URL for listing all payments
    path('lists/', views.payment_list, name='payment_list'),
    # URL for viewing a single payment detail
    path('list/<int:pk>/', views.payment_detail, name='payment_detail'),
]