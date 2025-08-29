from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # auth
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", views.logout_view, name="logout"),

    # customer registration
    path("register/", views.customer_register, name="customer_register"),

    # dashboards
    path("dashboard/", views.redirect_dashboard, name="redirect_dashboard"),
    path("dashboard/customer/", views.customer_dashboard, name="customer_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),

    #Pharmacist
    path("dashboard/pharmacist/", views.med_inventory_dash, name="med_inventory_dash"),

    #Cashier
    path("dashboard/cashier/", views.cashier_dashboard, name="cashier_dashboard"),

    # staff management
    path("dashboard/admin/create-staff/", views.create_staff, name="create_staff"),
    path("dashboard/admin/staff/", views.staff_list, name="staff_list"),
    path("dashboard/admin/staff/<int:staff_id>/edit/", views.edit_staff, name="edit_staff"),
    path("dashboard/admin/staff/<int:staff_id>/delete/", views.delete_staff, name="delete_staff"),
]