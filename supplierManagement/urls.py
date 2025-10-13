from django.urls import path
from . import views

app_name = "suppliers"

urlpatterns = [
    path('', views.SupplierListView.as_view(), name='list'),
    path('add/', views.SupplierCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='delete'),
    path('<int:pk>/', views.SupplierDetailView.as_view(), name='detail'),

        # Purchase orders
    path("purchase-orders/", views.PurchaseOrderListView.as_view(), name="purchase_order_list"),
    path("purchase-orders/new/", views.create_purchase_order, name="purchase_order_create"),
    path("purchase-items/<int:pk>/delete/", views.delete_purchase_item, name="purchase_item_delete"),
    path("orders/tracking/", views.order_tracking, name="order_tracking"),
    path("orders/history/", views.order_history, name="order_history"),
    path("orders/export/csv/", views.export_orders_csv, name="export_orders_csv"),
    path("orders/export/pdf/", views.export_orders_pdf, name="export_orders_pdf"),
    path("reports/supplier-daily-totals/", views.supplier_daily_totals, name="supplier_daily_totals"),
    path("reports/supplier-summary.pdf", views.generate_supplier_summary_pdf, name="supplier_summary_pdf"),
    path("orders/<int:pk>/status/", views.update_order_status, name="order_status_update"),
]