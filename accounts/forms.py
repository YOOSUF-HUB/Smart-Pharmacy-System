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
    # Make passwords optional for editing staff
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput, required=False)
    
    ROLE_CHOICES = (
        ('pharmacist', 'Pharmacist'),
        ('cashier', 'Cashier'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If instance exists (editing mode), make passwords optional
        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            # Make sure initial values are set
            self.initial['email'] = self.instance.email
            self.initial['role'] = self.instance.role

    def clean_username(self):
        username = self.cleaned_data['username']
        if self.instance and self.instance.pk:
            if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
        else:
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
        return username
        
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Always update these fields
        user.role = self.cleaned_data["role"]
        user.email = self.cleaned_data["email"]
        
        # Only set password if both password fields are provided
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
            
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