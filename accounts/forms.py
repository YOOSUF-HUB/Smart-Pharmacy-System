# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from .models import Customer, User

User = get_user_model()  # This gets your custom User model


class CustomerSignUpForm(UserCreationForm):
    """
    Form for customer registration with both User and Customer profile fields.
    Creates a new User with 'customer' role and associated Customer profile.
    """
    # User fields
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    
    # Customer profile fields
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'class': 'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-cyan-500 focus:ring-cyan-500'
        }), 
        required=False
    )
    city = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=20, required=False)
    country = forms.CharField(max_length=100, required=False)
    nic = forms.CharField(max_length=20, required=False, label="NIC Number")
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2", "first_name", "last_name")

    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        """Save user and create associated customer profile."""
        user = super().save(commit=False)
        user.role = "customer"
        user.email = self.cleaned_data.get('email')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        
        if commit:
            user.save()
            # Create customer profile with ALL fields
            Customer.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', ''),
                address=self.cleaned_data.get('address', ''),
                city=self.cleaned_data.get('city', ''),
                postal_code=self.cleaned_data.get('postal_code', ''),
                country=self.cleaned_data.get('country', ''),
                nic=self.cleaned_data.get('nic', '')
            )
        return user


class StaffCreationForm(forms.ModelForm):
    """
    Form for creating staff members (admin, pharmacist, cashier).
    Includes password confirmation and role selection.
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'date_hired', 'is_active')
        widgets = {
            'date_hired': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_password2(self):
        """Validate that password confirmation matches."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        """Save user with hashed password."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class StaffEditForm(forms.ModelForm):
    """
    Form for editing existing staff members.
    Does not include password fields - use separate password change form.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'date_hired', 'is_active')
        widgets = {
            'date_hired': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_date_hired(self):
        """Handle empty date strings."""
        date_hired = self.cleaned_data.get('date_hired')
        if date_hired == '':
            return None
        return date_hired


class CustomerProfileForm(forms.ModelForm):
    """
    Form for customers to edit their profile information.
    Includes both User fields and Customer profile fields.
    """
    # User fields
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = Customer
        fields = ['phone', 'address', 'city', 'postal_code', 'country', 'nic']
    
    def __init__(self, *args, **kwargs):
        """Initialize form with current user data."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def clean_username(self):
        """Validate username uniqueness (excluding current user)."""
        username = self.cleaned_data['username']
        if User.objects.exclude(pk=self.instance.user.pk).filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        """Save both User and Customer profile data."""
        profile = super().save(commit=False)
        user = profile.user
        
        # Update user fields
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # Update profile fields
        profile.phone = self.cleaned_data['phone']
        profile.address = self.cleaned_data['address']
        profile.city = self.cleaned_data['city']
        profile.postal_code = self.cleaned_data['postal_code']
        profile.country = self.cleaned_data['country']
        profile.nic = self.cleaned_data['nic']
        
        if commit:
            user.save()
            profile.save()
        return profile


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form with enhanced validation and user feedback.
    Provides specific error messages for different failure scenarios.
    """
    def __init__(self, *args, **kwargs):
        """Initialize form with custom styling."""
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })

    def clean(self):
        """Enhanced authentication validation with specific error messages."""
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                # Check if user exists
                user = User.objects.get(username=username)
                
                # Check if user is active
                if not user.is_active:
                    self.add_error(None, ValidationError(
                        "This account has been deactivated. Please contact your administrator.",
                        code='inactive_account'
                    ))
                    return self.cleaned_data
                
                # Try to authenticate
                self.user_cache = authenticate(
                    self.request, 
                    username=username, 
                    password=password
                )
                
                if self.user_cache is None:
                    # User exists but wrong password
                    raise ValidationError(
                        "Invalid password. Please check your password and try again.",
                        code='invalid_password'
                    )
                
            except User.DoesNotExist:
                # User doesn't exist
                raise ValidationError(
                    "No account found with this username. Please check your username or create a new account.",
                    code='user_not_found'
                )
        
        return self.cleaned_data