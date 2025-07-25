from django.urls import path
from . import views

urlpatterns = [
    path('', views.med_inventory_dashboard, name='med_inventory_dash'),  # Root now goes to dashboard
    path('medicine/cards/', views.view_medicine_cards, name='medicine_cards'),
    path('medicine/table/', views.view_medicine_table, name='medicine_table'),
    path('create/', views.create_medicine, name='medicine_create'), # Create new medicine
    path('update/<int:id>/', views.update_medicine, name='medicine_update'), # Update medicine by id
    path('delete/<int:id>/', views.delete_medicine, name='medicine_delete'), # Delete medicine by id
    path('export/csv/', views.export_medicine_csv, name='export_medicine_csv'),
    path('export/pdf/', views.export_medicine_pdf, name='export_medicine_pdf'),
]