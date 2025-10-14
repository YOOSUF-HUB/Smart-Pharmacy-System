# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.views.decorators.cache import never_cache
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.template.loader import render_to_string

# Python standard library imports
import csv
from datetime import datetime
from functools import wraps

# Third-party library imports
from weasyprint import HTML

# Local app imports
from .forms import (
    CustomerSignUpForm, 
    StaffCreationForm, 
    CustomerProfileForm, 
    StaffEditForm, 
    CustomAuthenticationForm
)
from .models import User, Customer


# =============================================================================
# DECORATORS
# =============================================================================


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != "admin":
            messages.error(request, "You do not have permission to access this page.")
            return redirect('account_not_found')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def pharmacist_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != "pharmacist":
            messages.error(request, "You do not have permission to access this page.")
            return redirect('account_not_found')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def cashier_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != "cashier":
            messages.error(request, "You do not have permission to access this page.")
            return redirect('account_not_found')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def customer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != "customer":
            messages.error(request, "You do not have permission to access this page.")
            return redirect('account_not_found')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def custom_403(request, exception):
    messages.error(request, "You do not have access to that page.")
    return redirect('account_not_found')


# =============================================================================
# ADMIN FUNCTIONS
# =============================================================================

# Admin dashboard view - displays main admin interface
@never_cache
@admin_required
def admin_dashboard(request):
    admin_count = User.objects.filter(role='admin').count()
    pharmacist_count = User.objects.filter(role='pharmacist').count()
    cashier_count = User.objects.filter(role='cashier').count()
    customer_count = User.objects.filter(role='customer').count()
    staff_count = admin_count + pharmacist_count + cashier_count
    inactive_account = User.objects.filter(is_active=False).count()

    context = {
        'admin_count': admin_count,
        'pharmacist_count': pharmacist_count,
        'cashier_count': cashier_count,
        'staff_count': staff_count,
        'customer_count': customer_count,
        'inactive_staff_count': inactive_account,
    }
    return render(request, "accounts/admin_dashboard.html", context)

# Create new staff member (pharmacist or cashier)
@admin_required
def create_staff(request):
    if request.method == "POST":
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            # Save user and set staff permissions
            user = form.save(commit=False)
            user.is_staff = True
            user.is_active = True
            user.save()
            messages.success(request, f'Staff member {user.username} created successfully.')
            return redirect("staff_list")
    else:
        form = StaffCreationForm()
    return render(request, "accounts/create_staff.html", {"form": form})

# Display list of all staff members
@admin_required
def staff_list(request):
    # Get only pharmacists and cashiers
    staff_users = User.objects.filter(role__in=["admin","pharmacist", "cashier"])
    inactive_account = User.objects.filter(is_active=False).count()

    context = {
        'inactive_account': inactive_account
    }
    return render(request, "accounts/staff_list.html", {"staff_users": staff_users, **context})

# Show detailed view of individual staff member
@admin_required
@never_cache
def staff_detail(request, staff_id):
    # Get staff member or return 404 if not found
    staff = get_object_or_404(User, id=staff_id, role__in=['admin', 'pharmacist', 'cashier'])
    
    context = {
        'staff': staff,
    }
    
    return render(request, 'accounts/staff_detail.html', context)

# Edit existing staff member details
@admin_required
def edit_staff(request, staff_id):
    staff = get_object_or_404(User, id=staff_id)
    
    if request.method == 'POST':
        print("POST data:", request.POST)
        form = StaffEditForm(request.POST, instance=staff)
        if form.is_valid():
            print("Form is valid")
            staff = form.save(commit=False)
            # Handle checkbox field for active status
            staff.is_active = 'is_active' in request.POST
            staff.save()
            messages.success(request, 'Staff account updated successfully')
            return redirect('staff_list')
        else:
            print("Form errors:", form.errors)
    else:
        # Load existing staff data into form
        form = StaffEditForm(instance=staff)
    
    return render(request, 'accounts/edit_staff.html', {'form': form})

# Delete staff member with confirmation
@admin_required
def delete_staff(request, staff_id):
    # Only allow deletion of pharmacists and cashiers
    staff_user = get_object_or_404(User, id=staff_id, role__in=["pharmacist", "cashier"])
    if request.method == "POST":
        # Confirm deletion
        staff_user.delete()
        messages.success(request, "Staff deleted successfully.")
        return redirect("staff_list")
    return render(request, "accounts/delete_staff.html", {"staff_user": staff_user})

# Display list of all customers
@admin_required
def customer_list(request):
    customers = User.objects.filter(role="customer")
    active_count = customers.filter(is_active=True).count()
    inactive_count = customers.filter(is_active=False).count()
    
    return render(request, "accounts/customer_list.html", {
        "customers": customers,
        "active_count": active_count,
        "inactive_count": inactive_count,
    })

# Show detailed view of individual customer
@admin_required
@never_cache
def customer_detail(request, customer_id):
    # Get both user and customer profile data
    customer_user = get_object_or_404(User, id=customer_id, role='customer')
    customer = get_object_or_404(Customer, user=customer_user)
    
    context = {
        'customer_user': customer_user,
        'customer': customer,
    }
    
    return render(request, 'accounts/customer_detail.html', context)

# Admin Export Functions
@login_required
@admin_required
def staff_list_csv(request):
    """Export staff list as CSV"""
    # Set up CSV response headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="staff_list.csv"'
    
    writer = csv.writer(response)
    # Write CSV header row
    writer.writerow(['Username', 'Email', 'Role', 'Status', 'Last Login', 'Date Joined'])
    
    # Get all staff users ordered by join date
    staff_users = User.objects.filter(role__in=["pharmacist", "cashier"]).order_by('-date_joined')
    
    # Write each staff member's data
    for staff in staff_users:
        # Format dates for display
        last_login = staff.last_login.strftime('%Y-%m-%d %H:%M:%S') if staff.last_login else 'Never'
        date_joined = staff.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        status = 'Active' if staff.is_active else 'Inactive'
        
        writer.writerow([
            staff.username,
            staff.email,
            staff.get_role_display() if hasattr(staff, 'get_role_display') else staff.role.title(),
            status,
            last_login,
            date_joined
        ])
    
    return response

# Export staff list as PDF file
@login_required
@admin_required
def staff_list_pdf(request):
    """Export staff list as PDF using WeasyPrint"""
    # Get all staff users for PDF
    staff_users = User.objects.filter(role__in=["pharmacist", "cashier"]).order_by('-date_joined')
    
    # Prepare context data for PDF template
    context = {
        'staff_users': staff_users,
        'generated_date': datetime.now().strftime('%B %d, %Y'),
        'generated_time': datetime.now().strftime('%I:%M %p'),
        'total_staff': staff_users.count(),
    }
    
    # Generate HTML from template
    html_string = render_to_string('accounts/staff_list_pdf.html', context)
    
    # Convert HTML to PDF
    try:
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        # Return PDF as downloadable file
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="staff_list.pdf"'
        
        return response
    except Exception as e:
        # Handle PDF generation errors
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('staff_list')


# =============================================================================
# ROLE-BASED DASHBOARD FUNCTIONS
# =============================================================================

@never_cache
@pharmacist_required
def med_inventory_dash(request):
    return render(request, "Medicine_inventory/med_inventory_dash.html")

@never_cache
@cashier_required
def cashier_dashboard(request):
    return render(request, "accounts/cashier_dashboard.html")

@never_cache
@customer_required
@login_required
def customer_dashboard(request):
    if request.user.role != 'customer':
        messages.error(request, "You don't have permission to access the customer dashboard.")
        return redirect('login')
    
    # Create a context dictionary
    context = {
        'user': request.user,
        # Add any other data you want to display in the dashboard
    }
    
    # Rest of your customer dashboard code...
    return render(request, 'accounts/customer_dashboard.html', context)

@login_required
def redirect_dashboard(request):
    user = request.user
    if user.role == "admin":
        return redirect("admin_dashboard")
    elif user.role == "pharmacist":
        return redirect("med_inventory_dash")
    elif user.role == "cashier":
        return redirect("cashier_dashboard")
    else:
        return redirect("account_not_found")


# =============================================================================
# CUSTOMER FUNCTIONS
# =============================================================================

# Handle customer registration process
def customer_register(request):
    if request.method == "POST":
        # Process registration form submission
        form = CustomerSignUpForm(request.POST)
        if form.is_valid():
            try:
                # Save new customer user
                user = form.save()
                # Automatically log in the user after successful registration
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect("customer_dashboard")
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Display empty registration form for GET request
        form = CustomerSignUpForm()
    return render(request, "accounts/register.html", {"form": form})

# Allow customers to edit their profile information
@customer_required
def edit_customer_profile(request):
    try:
        # Try to get existing customer profile
        customer = request.user.customer
    except Customer.DoesNotExist:
        # Create customer profile if it doesn't exist
        customer = Customer.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Process profile update form submission
        form = CustomerProfileForm(request.POST, instance=customer)
        print("Form data:", request.POST)  # Debug: log form data
        if form.is_valid():
            print("Form is valid")  # Debug: confirm form validation
            # Save the updated profile
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('customer_dashboard')
        else:
            print("Form errors:", form.errors)  # Debug: log any form errors
    else:
        # Load existing customer data into form for GET request
        form = CustomerProfileForm(instance=customer)
    
    return render(request, 'accounts/edit_customer_profile.html', {'form': form})


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def inactive_account(request):
    return render(request, 'accounts/inactive_account.html')

def account_not_found(request):
    return render(request, "accounts/account_not_found.html")

def protected_view(request):
    if not some_condition:
        raise PermissionDenied
    # Rest of your view

def test_password_reset(request):
    """Simple test view to verify URL configuration"""
    return HttpResponse("Password reset URLs are configured correctly!")


# =============================================================================
# LOGIN/LOGOUT AND AUTHENTICATION FUNCTIONS
# =============================================================================

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    form_class = CustomAuthenticationForm
    
    def form_invalid(self, form):
        # Check if the specific inactive error is present
        if any('inactive_account' == err.code for err in form.non_field_errors().data):
            return redirect('inactive_account')
        return super().form_invalid(form)

class CustomerLoginView(LoginView):
    template_name = 'accounts/customer_login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('onlineStore:homepage')
    
    def form_valid(self, form):
        """Check if the user is a customer before logging in"""
        user = form.get_user()
        if user.role != 'customer':
            messages.error(self.request, "This login is for customers only. Please use the staff login page.")
            return self.form_invalid(form)
        
        messages.success(self.request, 'Login successful!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle invalid login attempts"""
        # Add a custom error message for invalid credentials
        if form.errors:
            messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)
        
    def get_success_url(self):
        return reverse_lazy('onlineStore:homepage')

class StaffPasswordResetView(PasswordResetView):
    """Custom password reset view that only allows staff users to reset passwords"""
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        
        # Check if any active staff user exists with this email
        staff_users = User.objects.filter(email=email, is_staff=True, is_active=True)
        
        if not staff_users.exists():
            # Check if any user exists with this email but is not staff
            non_staff_users = User.objects.filter(email=email, is_active=True)
            
            if non_staff_users.exists():
                # User exists but is not staff
                messages.error(self.request, 'Password reset is only available for staff members. Please contact your administrator.')
                return redirect('password_reset')
            else:
                # No user exists with this email (don't reveal this for security)
                messages.error(self.request, 'If a staff account with this email exists, you will receive a password reset link.')
                return redirect('password_reset')
        
        # If we get here, there are active staff users with this email
        # Proceed with the normal password reset process
        return super().form_valid(form)

    def get_users(self, email):
        """Override to only return active staff users"""
        return User.objects.filter(
            email__iexact=email,
            is_active=True,
            is_staff=True
        )

@never_cache
def logout_view(request):
    logout(request)
    response = redirect('login')
    # Set cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
def customer_logout_view(request):
    """Custom logout view for customers with success message"""
    if request.user.is_authenticated and request.user.role == 'customer':
        username = request.user.first_name or request.user.username
        logout(request)
        messages.success(
            request, f"Goodbye {username}! You have been successfully logged out.")
    else:
        logout(request)
        messages.info(request, "You have been logged out.")

    response = redirect('onlineStore:homepage')
    # Set cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def custom_404(request, exception):
    return redirect('account_not_found')

@admin_required
def export_customers_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'Phone', 'Address', 'Status', 'Date Joined'])
    for c in User.objects.filter(role='customer').select_related('customer'):
        writer.writerow([c.id, c.username, c.email, c.customer.phone or 'N/A', c.customer.address or 'N/A', 'Active' if c.is_active else 'Inactive', c.date_joined.strftime('%Y-%m-%d')])
    return response

@admin_required
def export_customers_pdf(request):
    customers = User.objects.filter(role='customer').select_related('customer')
    html_string = render_to_string('accounts/customers_pdf.html', {'customers': customers})
    html = HTML(string=html_string)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="customers.pdf"'
    html.write_pdf(response)
    return response