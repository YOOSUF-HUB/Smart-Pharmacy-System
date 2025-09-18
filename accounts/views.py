from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.conf import settings
from functools import wraps
from django.core.exceptions import PermissionDenied
from .forms import CustomerSignUpForm, StaffCreationForm, CustomerProfileForm, StaffEditForm, CustomAuthenticationForm
from .models import User, Customer
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.http import HttpResponse


def inactive_account(request):
    return render(request, 'accounts/inactive_account.html')

def protected_view(request):
    if not some_condition:
        raise PermissionDenied
    # Rest of your view

# Decorators
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != "admin":
            raise PermissionDenied("You must be an admin to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def pharmacist_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != "pharmacist":
            raise PermissionDenied("You must be a pharmacist to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def cashier_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != "cashier":
            raise PermissionDenied("You must be a cashier to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def customer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != "customer":
            raise PermissionDenied("You must be a customer to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# dashboards
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

@never_cache
@admin_required
def admin_dashboard(request):
    return render(request, "accounts/admin_dashboard.html")

@never_cache
@pharmacist_required
def med_inventory_dash(request):
    return render(request, "Medicine_inventory/med_inventory_dash.html")

@never_cache
@cashier_required
def cashier_dashboard(request):
    return render(request, "accounts/cashier_dashboard.html")

@login_required
def redirect_dashboard(request):
    user = request.user
    if user.role == "customer":
        return redirect("customer_dashboard")
    elif user.role == "admin":
        return redirect("admin_dashboard")
    elif user.role == "pharmacist":
        return redirect("med_inventory_dash")
    elif user.role == "cashier":
        return redirect("cashier_dashboard")



@admin_required
def create_staff(request):
    if request.method == "POST":
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True  # Ensure this line exists
            user.is_active = True  # Also ensure they're active
            user.save()
            messages.success(request, f'Staff member {user.username} created successfully.')
            return redirect("staff_list")
    else:
        form = StaffCreationForm()
    return render(request, "accounts/create_staff.html", {"form": form})

@admin_required
def staff_list(request):
    staff_users = User.objects.filter(role__in=["pharmacist", "cashier"])
    return render(request, "accounts/staff_list.html", {"staff_users": staff_users})

@admin_required
def edit_staff(request, staff_id):
    staff = get_object_or_404(User, id=staff_id)
    
    if request.method == 'POST':
        print("POST data:", request.POST)
        form = StaffEditForm(request.POST, instance=staff)
        if form.is_valid():
            print("Form is valid")
            staff = form.save(commit=False)
            # Make sure is_active is properly handled since it's a checkbox
            staff.is_active = 'is_active' in request.POST
            staff.save()
            messages.success(request, 'Staff account updated successfully')
            return redirect('staff_list')
        else:
            print("Form errors:", form.errors)
    else:
        form = StaffEditForm(instance=staff)
    
    return render(request, 'accounts/edit_staff.html', {'form': form})

@admin_required
def delete_staff(request, staff_id):
    staff_user = get_object_or_404(User, id=staff_id, role__in=["pharmacist", "cashier"])
    if request.method == "POST":
        staff_user.delete()
        messages.success(request, "Staff deleted successfully.")
        return redirect("staff_list")
    return render(request, "accounts/delete_staff.html", {"staff_user": staff_user})

@never_cache
def logout_view(request):
    logout(request)
    response = redirect('login')
    # Set cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@admin_required
def customer_list(request):
    customers = User.objects.filter(role="customer")
    return render(request, "accounts/customer_list.html", {"customers": customers})


@admin_required
@never_cache
def customer_detail(request, customer_id):
    customer_user = get_object_or_404(User, id=customer_id, role='customer')
    customer = get_object_or_404(Customer, user=customer_user)
    
    context = {
        'customer_user': customer_user,
        'customer': customer,
    }
    
    return render(request, 'accounts/customer_detail.html', context)





#Customer View Sections

@customer_required
def edit_customer_profile(request):
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        # Create customer profile if it doesn't exist
        customer = Customer.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=customer)
        print("Form data:", request.POST)
        if form.is_valid():
            print("Form is valid")
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('customer_dashboard')
        else:
            print("Form errors:", form.errors)
    else:
        form = CustomerProfileForm(instance=customer)
    
    return render(request, 'accounts/edit_customer_profile.html', {'form': form})


# customer self registration
def customer_register(request):
    if request.method == "POST":
        form = CustomerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto login after registration
            return redirect("customer_dashboard")
    else:
        form = CustomerSignUpForm()
    return render(request, "accounts/register.html", {"form": form})





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
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('onlineStore:homepage')

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




@admin_required
@never_cache
def staff_detail(request, staff_id):
    staff = get_object_or_404(User, id=staff_id, role__in=['admin', 'pharmacist', 'cashier'])
    
    context = {
        'staff': staff,
    }
    
    return render(request, 'accounts/staff_detail.html', context)


def test_password_reset(request):
    """Simple test view to verify URL configuration"""
    return HttpResponse("Password reset URLs are configured correctly!")

class StaffPasswordResetView(PasswordResetView):
    """Custom password reset view"""
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

class StaffPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view"""
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')