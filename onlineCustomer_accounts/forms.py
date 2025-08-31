from django import forms

from accounts.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm

from .models import Customer


class CreateAccountForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False)
    address = forms.CharField(required=False)

    class Meta:
        model = User  # IMPORTANT: Use User, not Customer
        fields = ['username', 'email', 'password1', 'password2', 'phone', 'address']

        
    def save(self, commit=True):
        user = super().save(commit=commit)
        # Create Customer profile linked to this User
        Customer.objects.create(
            user=user,
            phone=self.cleaned_data.get('phone'),
            address=self.cleaned_data.get('address')
        )
        return user
    

class CustomerLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )