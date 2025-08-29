# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "customer"   # default role
        if commit:
            user.save()
        return user



class StaffCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('pharmacist', 'Pharmacist'),
        ('cashier', 'Cashier'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user