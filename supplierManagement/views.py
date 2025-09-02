from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .models import Supplier, Product
from .forms import SupplierForm, ProductForm


class SupplierListView(ListView):
    model = Supplier
    template_name = "supplierManagement/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 10

    def get_queryset(self):
        qs = Supplier.objects.all().prefetch_related("products")
        q = self.request.GET.get("q", "").strip()
        product_type = self.request.GET.get("product_type", "").strip()
        status = self.request.GET.get("status", "").strip()

        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(contact_person__icontains=q)
            )

        if product_type:
            qs = qs.filter(products__category=product_type)

        if status:
            qs = qs.filter(status__iexact=status.capitalize())

        qs = qs.annotate(num_products=Count("products", distinct=True)).order_by("name")
        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Get unique product categories from Product model
        ctx["product_types"] = Product.objects.values_list(
            "category", flat=True
        ).distinct().order_by("category")
        ctx["current_q"] = self.request.GET.get("q", "")
        ctx["current_product_type"] = self.request.GET.get("product_type", "")
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


class SupplierCreateView(CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "supplierManagement/supplier_form.html"
    success_url = reverse_lazy("suppliers:list")


class SupplierUpdateView(UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "supplierManagement/supplier_form.html"
    success_url = reverse_lazy("suppliers:list")


class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = "supplierManagement/supplier_confirm_delete.html"
    success_url = reverse_lazy("suppliers:list")


class SupplierDetailView(DetailView):
    model = Supplier
    template_name = "supplierManagement/supplier_detail.html"
    context_object_name = "supplier"