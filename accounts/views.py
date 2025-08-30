from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import LoginView

from .forms import CustomerSignUpForm, StaffCreationForm, CustomerProfileForm
from .models import User, Customer

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


# Add these near your admin_required decorator

def pharmacist_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "pharmacist")(view_func)

def cashier_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "cashier")(view_func)

def customer_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "customer")(view_func)

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "admin")(view_func)

# dashboards
@never_cache
@customer_required
def customer_dashboard(request):
    return render(request, "accounts/customer_dashboard.html")

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
            form.save()
            return redirect("admin_dashboard")
    else:
        form = StaffCreationForm()
    return render(request, "accounts/create_staff.html", {"form": form})

@admin_required
def staff_list(request):
    staff_users = User.objects.filter(role__in=["pharmacist", "cashier"])
    return render(request, "accounts/staff_list.html", {"staff_users": staff_users})

@admin_required
def edit_staff(request, staff_id):
    staff_user = get_object_or_404(User, id=staff_id, role__in=["pharmacist", "cashier"])
    
    if request.method == "POST":
        form = StaffCreationForm(request.POST, instance=staff_user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Staff member {staff_user.username} has been updated.")
            return redirect('staff_list')
    else:
        form = StaffCreationForm(instance=staff_user)
    
    return render(request, "accounts/edit_staff.html", {"form": form})

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

def edit_customer_profile(request):
    # Get or create the customer profile
    customer, created = Customer.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('customer_dashboard')
        else:
            # If form is invalid, show error message
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerProfileForm(instance=customer)
    
    return render(request, 'accounts/edit_customer_profile.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already authenticated, redirect to appropriate dashboard
        if request.user.is_authenticated:
            return redirect('redirect_dashboard')
        return super().dispatch(request, *args, **kwargs)