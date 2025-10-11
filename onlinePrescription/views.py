from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django import forms
from django.core.exceptions import ValidationError

from .models import Prescription
from onlineStore.models import Order

# Role check for pharmacists (match your user.role implementation)
pharmacist_required = user_passes_test(
    lambda u: u.is_authenticated and getattr(u, "role", "") == "pharmacist")

# ---------- Forms ----------
class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["prescription_image", "notes", "nic", "order"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit order choices to this user's orders that don't already have a prescription
        if user is not None:
            self.fields["order"].queryset = Order.objects.filter(
                customer_user=user
            ).exclude(prescription__isnull=False)
        else:
            self.fields["order"].queryset = Order.objects.none()

    def clean_prescription_image(self):
        image = self.cleaned_data.get("prescription_image")
        if image:
            content_type = image.content_type
            if not content_type.startswith("image/"):
                raise ValidationError("Upload must be an image file (jpg/png).")
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file too large (max 5MB).")
        return image


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["status", "pharmacist_comment"]


# ---------- Customer Views ----------
@method_decorator(login_required, name="dispatch")
class PrescriptionCreateView(CreateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = "onlinePrescription/prescription_form.html"
    success_url = reverse_lazy("onlineStore:cart")  # change to desired url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Prescription uploaded successfully.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "There was a problem uploading the prescription.")
        return super().form_invalid(form)


@method_decorator(login_required, name="dispatch")
class PrescriptionListView(ListView):
    model = Prescription
    template_name = "onlinePrescription/prescription_list.html"
    context_object_name = "prescriptions"
    paginate_by = 12

    def get_queryset(self):
        return Prescription.objects.filter(user=self.request.user).order_by("-uploaded_at")


@method_decorator(login_required, name="dispatch")
class PrescriptionDetailView(DetailView):
    model = Prescription
    template_name = "onlinePrescription/prescription_detail.html"
    context_object_name = "prescription"

    def get_queryset(self):
        # allow owner or pharmacists
        qs = super().get_queryset()
        if getattr(self.request.user, "role", "") == "pharmacist":
            return qs
        return qs.filter(user=self.request.user)


@method_decorator(login_required, name="dispatch")
class PrescriptionDeleteView(DeleteView):
    model = Prescription
    template_name = "onlinePrescription/prescription_confirm_delete.html"
    success_url = reverse_lazy("onlinePrescription:list")

    def get_queryset(self):
        # only owner may delete
        return Prescription.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Prescription deleted.")
        return super().delete(request, *args, **kwargs)


# ---------- Pharmacist Views ----------
@method_decorator(pharmacist_required, name="dispatch")
class PharmacistPrescriptionListView(ListView):
    model = Prescription
    template_name = "onlinePrescription/pharmacist_prescription_list.html"
    context_object_name = "prescriptions"
    paginate_by = 20

    def get_queryset(self):
        # optional filter by status via GET param
        status = self.request.GET.get("status")
        qs = Prescription.objects.all().order_by("-uploaded_at")
        if status:
            qs = qs.filter(status__iexact=status)
        return qs


@method_decorator(pharmacist_required, name="dispatch")
class PharmacistPrescriptionDetailView(DetailView):
    model = Prescription
    template_name = "onlinePrescription/pharmacist_prescription_detail.html"
    context_object_name = "prescription"


@method_decorator(pharmacist_required, name="dispatch")
class PharmacistPrescriptionReviewView(UpdateView):
    model = Prescription
    form_class = ReviewForm
    template_name = "onlinePrescription/pharmacist_review_form.html"

    def get_success_url(self):
        messages.success(self.request, "Prescription updated.")
        return reverse("onlinePrescription:pharmacist_list")

    def form_valid(self, form):
        return super().form_valid(form)