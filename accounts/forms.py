# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Customer  # Use your actual model name

User = get_user_model()  # This gets your custom User model

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


class StaffCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('pharmacist', 'Pharmacist'),
        ('cashier', 'Cashier'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'role']

    def clean_username(self):
        username = self.cleaned_data['username']
        # Check if this instance exists (editing an existing user)
        if self.instance and self.instance.pk:
            # Exclude the current user from the uniqueness check
            if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
        else:
            # For new users, check if username exists
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
        return username
        
    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        user.set_password(self.cleaned_data["password1"])  # This properly hashes the password
        if commit:
            user.save()
        return user


class CustomerProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Customer
        fields = ['phone', 'address']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            # Initialize all fields with current user data
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            
    def clean_username(self):
        username = self.cleaned_data['username']
        # Using the custom User model via get_user_model()
        if User.objects.exclude(pk=self.instance.user.pk).filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        
        # Update user fields
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
        return profile