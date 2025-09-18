from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

urlpatterns = [
    # auth
    path('', CustomLoginView.as_view(), name='login'),
    path("logout/", views.logout_view, name="logout"),

    # customer registration
    path("register/", views.customer_register, name="customer_register"),
    path('customer-login/', views.CustomerLoginView.as_view(), name='customer_login'),

    # dashboards
    path("dashboard/", views.redirect_dashboard, name="redirect_dashboard"),
    path("dashboard/customer/", views.customer_dashboard, name="customer_dashboard"),
    path("dashboard/customer/edit-profile/", views.edit_customer_profile, name="edit_customer_profile"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path('accounts/inactive-account/', views.inactive_account, name='inactive_account'),
    
    #Pharmacist
    path("dashboard/pharmacist/", views.med_inventory_dash, name="med_inventory_dash"),

    #Cashier
    path("dashboard/cashier/", views.cashier_dashboard, name="cashier_dashboard"),

    # staff management
    path("dashboard/admin/create-staff/", views.create_staff, name="create_staff"),
    path("dashboard/admin/staff/", views.staff_list, name="staff_list"),
    path("dashboard/admin/staff/<int:staff_id>/edit/", views.edit_staff, name="edit_staff"),
    path("dashboard/admin/staff/<int:staff_id>/delete/", views.delete_staff, name="delete_staff"),
    path("dashboard/admin/customers/", views.customer_list, name="customer_list"),
    path('dashboard/admin/customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('dashboard/admin/staff_detail/<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('customer-logout/', views.customer_logout_view, name='customer_logout'),

    # Password Reset URLs - ADD THESE NEW LINES
    path('test-reset/', views.test_password_reset, name='test_password_reset'),
    path('password-reset/', views.StaffPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.StaffPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]