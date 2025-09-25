from django.urls import path
from Pharmarcy_Prescription_Tracker import settings
from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static






urlpatterns = [
    path('', views.med_inventory_dash, name='med_inventory_dash'),
    path('medicine/cards/', views.view_medicine_cards, name='medicine_cards'),
    path('medicine/table/', views.view_medicine_table, name='medicine_table'),
    path('create/', views.create_medicine, name='medicine_create'),
    path('update/<int:id>/', views.update_medicine, name='medicine_update'),
    path('delete/<int:id>/', views.delete_medicine, name='medicine_delete'),
    path('export/csv/', views.export_medicine_csv, name='export_medicine_csv'),
    path('export/pdf/', views.export_medicine_pdf, name='export_medicine_pdf'),
    path('medicine/<int:id>/', views.medicine_detail, name='medicine_detail'),
    # Remove this line: path('accounts/', include('accounts.urls')),
    path('medicines/bulk_upload/', views.bulk_upload_medicines, name='bulk_upload_medicines'),

    path('online-orders/', views.view_online_orders, name='view_online_orders'),
    path('order/<str:order_id>/', views.order_detail, name='order_detail'),
    path('order/<str:order_id>/update-status/', views.update_order_status, name='update_order_status'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)