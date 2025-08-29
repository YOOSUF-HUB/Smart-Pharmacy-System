# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomerSignUpForm
from .models import User
from django.contrib.auth.decorators import user_passes_test
from .forms import StaffCreationForm
from django.contrib.auth import logout
from django.shortcuts import redirect

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

# dashboards
def customer_dashboard(request):
    return render(request, "accounts/customer_dashboard.html")

def admin_dashboard(request):
    return render(request, "accounts/admin_dashboard.html")

def pharmacist_dashboard(request):
    return render(request, "accounts/pharmacist_dashboard.html")

def cashier_dashboard(request):
    return render(request, "accounts/cashier_dashboard.html")


# accounts/views.py
from django.contrib.auth.decorators import login_required

@login_required
def redirect_dashboard(request):
    user = request.user
    if user.role == "customer":
        return redirect("customer_dashboard")
    elif user.role == "admin":
        return redirect("admin_dashboard")
    elif user.role == "pharmacist":
        return redirect("pharmacist_dashboard")
    elif user.role == "cashier":
        return redirect("cashier_dashboard")


def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "admin")(view_func)

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





from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .forms import StaffCreationForm
from .models import User


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
            messages.success(request, "Staff updated successfully.")
            return redirect("staff_list")
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


def logout_view(request):
    logout(request)
    return redirect('login')