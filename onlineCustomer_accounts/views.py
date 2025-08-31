from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout


from .forms import CreateAccountForm
from .forms import CustomerLoginForm

# Create your views here.

def create_account(request):
    if request.method == "POST":
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("onlineStore:homepage")

    else:
        form = CreateAccountForm()
    return render(request, "onlineCustomer_accounts/createAccount.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("onlineStore:homepage")
    else:
        form = CustomerLoginForm()
    
    return render(request, "onlineCustomer_accounts/login.html", {"form": form})

def user_logout(request):
    logout(request)
    return redirect("onlineStore:homepage")