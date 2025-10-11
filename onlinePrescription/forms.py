from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings

from .models import Prescription
from onlineStore.models import Order

from django.core.validators import RegexValidator

NIC_REGEX = r'^(?:\d{9}[VvXx]|\d{12})$'
nic_validator = RegexValidator(NIC_REGEX,message="Enter a valid Sri Lankan NIC (old: 9 digits + V/v/X, or new: 12 digits).")


MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["prescription_image", "notes", "nic", "order"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit order choices to this user's orders that don't already have a prescription
        if user is not None:
            self.fields["order"].queryset = Order.objects.filter(customer_user=user).exclude(prescription__isnull=False)
        else:
            self.fields["order"].queryset = Order.objects.none()

    def clean_prescription_image(self):
        image = self.cleaned_data.get("prescription_image")
        if not image:
            raise ValidationError("An image file is required.")
        content_type = getattr(image, "content_type", "")
        if not content_type.startswith("image/"):
            raise ValidationError("Uploaded file must be an image (JPEG/PNG/etc.).")
        if image.size > MAX_UPLOAD_SIZE:
            raise ValidationError("Image file too large (max 5 MB).")
        return image

    def clean_nic(self):
        nic = self.cleaned_data.get("nic", "").strip()
        nic_validator(nic)
        return nic


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["status", "pharmacist_comment"]
        widgets = {
            "pharmacist_comment": forms.Textarea(attrs={"rows": 3}),
        }