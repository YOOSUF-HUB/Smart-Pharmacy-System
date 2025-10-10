from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect

from .models import Supplier, Product
from .forms import SupplierForm, ProductForm

# Decorator to restrict access to pharmacists only
pharmacist_required = user_passes_test(
    lambda u: u.is_authenticated and getattr(u, "role", "") == "pharmacist"
)

# ============================
# Supplier Views
# ============================

@method_decorator(pharmacist_required, name="dispatch")
class SupplierListView(ListView):
    """Display a paginated list of suppliers with search and filters"""
    model = Supplier
    template_name = "supplierManagement/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 10

    def get_queryset(self):
        """Filter suppliers based on search query, product type, and status"""
        qs = Supplier.objects.all().prefetch_related("products")
        q = self.request.GET.get("q", "").strip()
        product_type = self.request.GET.get("product_type", "").strip()
        status = self.request.GET.get("status", "").strip()

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(contact_person__icontains=q))
        if product_type:
            qs = qs.filter(products__category=product_type)
        if status:
            qs = qs.filter(status__iexact=status.capitalize())

        # Annotate with number of products and order by supplier name
        qs = qs.annotate(num_products=Count("products", distinct=True)).order_by("name")
        return qs.distinct()

    def get_context_data(self, **kwargs):
        """Add extra context for the template (filters and search query)"""
        ctx = super().get_context_data(**kwargs)
        ctx["product_types"] = Product.objects.values_list("category", flat=True).distinct().order_by("category")
        ctx["current_q"] = self.request.GET.get("q", "")
        ctx["current_product_type"] = self.request.GET.get("product_type", "")
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


@method_decorator(pharmacist_required, name="dispatch")
class SupplierCreateView(CreateView):
    """Form to create a new supplier"""
    model = Supplier
    form_class = SupplierForm
    template_name = "supplierManagement/supplier_form.html"
    success_url = reverse_lazy("suppliers:list")


@method_decorator(pharmacist_required, name="dispatch")
class SupplierUpdateView(UpdateView):
    """Form to update an existing supplier"""
    model = Supplier
    form_class = SupplierForm
    template_name = "supplierManagement/supplier_form.html"
    success_url = reverse_lazy("suppliers:list")


@method_decorator(pharmacist_required, name="dispatch")
class SupplierDeleteView(DeleteView):
    """Delete a supplier with proper error handling for protected records"""
    model = Supplier
    success_url = reverse_lazy("suppliers:list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        try:
            # Attempt to delete supplier
            response = super().post(request, *args, **kwargs)
            messages.success(request, f'Supplier "{name}" deleted successfully.')
            return response
        except ProtectedError:
            # Handle cases where supplier is linked to products or other records
            messages.error(request, f'Cannot delete "{name}" because it is referenced by other records.')
            return redirect(self.success_url)


@method_decorator(pharmacist_required, name="dispatch")
class SupplierDetailView(DetailView):
    """Display detailed information about a supplier"""
    model = Supplier
    template_name = "supplierManagement/supplier_detail.html"
    context_object_name = "supplier"
