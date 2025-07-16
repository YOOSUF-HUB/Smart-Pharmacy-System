from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_medicine, name='medicine_list'),          # List all medicines
    path('create/', views.create_medicine, name='medicine_create'), # Create new medicine
    path('update/<int:id>/', views.update_medicine, name='medicine_update'), # Update medicine by id
    path('delete/<int:id>/', views.delete_medicine, name='medicine_delete'), # Delete medicine by id
]