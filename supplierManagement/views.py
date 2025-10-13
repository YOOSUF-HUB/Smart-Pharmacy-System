from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.forms import modelformset_factory
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv

# PDF/report helpers
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .models import Supplier, Product, PurchaseOrder, PurchaseOrderItem  # add models
from .forms import SupplierForm, ProductForm, PurchaseOrderForm, PurchaseOrderItemForm, PurchaseOrderStatusForm  # add forms

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


# ============================
# Purchase Order Views
# ============================

@method_decorator(pharmacist_required, name="dispatch")
class PurchaseOrderListView(ListView):
    """List purchase orders with supplier and items preloaded"""
    model = PurchaseOrder
    template_name = "supplierManagement/purchase_order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return (
            PurchaseOrder.objects.select_related("supplier")
            .prefetch_related("items__product")
            .order_by("-id")
        )


@pharmacist_required
def create_purchase_order(request):
    ItemFormSet = modelformset_factory(PurchaseOrderItem, form=PurchaseOrderItemForm, extra=1, can_delete=True)

    if request.method == "POST":
        order_form = PurchaseOrderForm(request.POST)
        formset = ItemFormSet(request.POST, queryset=PurchaseOrderItem.objects.none())

        # Detect at least one non-empty row (before validation)
        def _has_input(f):
            data = f.data
            px = f.prefix
            name = (data.get(f"{px}-product_name") or "").strip()
            qty = (data.get(f"{px}-quantity") or "").strip()
            price = (data.get(f"{px}-price") or "").strip()
            delete = data.get(f"{px}-DELETE") in ("on", "true", "1")
            return (name or qty or price) and not delete

        has_any_row = any(_has_input(f) for f in formset.forms)

        if not has_any_row:
            messages.error(request, "Please add at least one product to the order.")
        elif order_form.is_valid() and formset.is_valid():
            purchase_order = order_form.save(commit=False)
            purchase_order.total_cost = 0
            purchase_order.save()

            total = 0
            for f in formset.forms:
                if f.cleaned_data and not f.cleaned_data.get("DELETE", False):
                    item = f.save(commit=False)  # sets item.product in form.save()
                    item.purchase_order = purchase_order
                    item.save()
                    total += item.get_subtotal()

            purchase_order.total_cost = total
            purchase_order.save()
            messages.success(request, "Purchase order created successfully!")
            list_url = reverse("suppliers:purchase_order_list")
            return redirect(list_url)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        order_form = PurchaseOrderForm()
        formset = ItemFormSet(queryset=PurchaseOrderItem.objects.none())

    return render(request, "supplierManagement/purchase_order_form.html", {
        "order_form": order_form,
        "formset": formset,
        "products": Product.objects.all()
    })


@pharmacist_required
def delete_purchase_item(request, pk):
    """
    Remove a single PurchaseOrderItem. POST only.
    """
    item = get_object_or_404(PurchaseOrderItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Item removed from the purchase order.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect("suppliers:purchase_order_list")


@pharmacist_required
def order_tracking(request):
    """
    Filter purchase orders by status and supplier name.
    """
    status = request.GET.get("status")
    supplier = request.GET.get("supplier")

    orders = PurchaseOrder.objects.select_related("supplier").prefetch_related("items")

    if status:
        orders = orders.filter(status=status)
    if supplier:
        orders = orders.filter(supplier__name__icontains=supplier)

    return render(
        request,
        "supplierManagement/order_tracking.html",
        {
            "orders": orders,
            "current_status": status,
            "current_supplier": supplier,
            "status_choices": getattr(PurchaseOrder, "STATUS_CHOICES", ()),
        },
    )


@pharmacist_required
def order_history(request):
    """
    Reports page with optional start/end date and supplier filters.
    """
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    supplier = request.GET.get("supplier")

    orders = PurchaseOrder.objects.select_related("supplier")

    if start_date and end_date:
        orders = orders.filter(order_date__range=[start_date, end_date])
    if supplier:
        orders = orders.filter(supplier__name__icontains=supplier)

    return render(
        request,
        "supplierManagement/order_history.html",
        {
            "orders": orders,
            "current_supplier": supplier,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@pharmacist_required
def export_orders_csv(request):
    """
    Export all purchase orders to CSV.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="order_history.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ["Order ID", "Supplier", "Order Date", "Expected Delivery", "Status", "Total Cost"]
    )

    orders = PurchaseOrder.objects.all().select_related("supplier")
    for order in orders:
        writer.writerow(
            [
                order.id,
                order.supplier.name if order.supplier_id else "",
                order.order_date,
                getattr(order, "expected_delivery", ""),
                order.status,
                order.total_cost,
            ]
        )
    return response


@pharmacist_required
def export_orders_pdf(request):
    """
    Export all purchase orders to a simple PDF table.
    """
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="order_history.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Header
    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, height - 40, "Order History Report")

    # Table header
    p.setFont("Helvetica-Bold", 10)
    y = height - 80
    headers = ["Order ID", "Supplier", "Order Date", "Expected Delivery", "Status", "Total Cost"]
    x_list = [30, 90, 220, 340, 460, 540]
    for x, header in zip(x_list, headers):
        p.drawString(x, y, header)

    # Rows
    orders = PurchaseOrder.objects.select_related("supplier").all().order_by("id")
    p.setFont("Helvetica", 10)
    y -= 20
    for order in orders:
        p.drawString(x_list[0], y, str(order.id))
        p.drawString(x_list[1], y, order.supplier.name if order.supplier_id else "")
        p.drawString(x_list[2], y, str(order.order_date))
        p.drawString(x_list[3], y, str(getattr(order, "expected_delivery", "")))
        p.drawString(x_list[4], y, order.status)
        p.drawString(x_list[5], y, str(order.total_cost))
        y -= 18
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 60

    p.showPage()
    p.save()
    return response


@pharmacist_required
def supplier_daily_totals(request):
    """
    Groups purchase orders by supplier and date, sums total_cost.
    """
    from django.db.models import Sum

    totals = (
        PurchaseOrder.objects.values("supplier__name", "order_date")
        .annotate(total_amount=Sum("total_cost"))
        .order_by("-order_date", "supplier__name")
    )
    return render(
        request,
        "supplierManagement/supplier_daily_totals.html",
        {"totals": totals},
    )


@pharmacist_required
def generate_supplier_summary_pdf(request):
    """
    For each supplier, list purchased items with subtotal and per-supplier total.
    """
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="supplier_summary_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph("Supplier Summary Report", styles["h1"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    suppliers = Supplier.objects.prefetch_related("purchase_orders__items__product").all()

    for supplier in suppliers:
        elements.append(Paragraph(f"Supplier: {supplier.name}", styles["h2"]))

        data = [["Product Name", "Quantity", "Unit Price", "Subtotal"]]
        total_for_supplier = 0

        for order in supplier.purchase_orders.all():
            for item in order.items.all():
                product_name = item.product.name if item.product_id else "-"
                quantity = item.quantity
                unit_price = getattr(item, "price", 0)
                subtotal = getattr(item, "get_subtotal", lambda: quantity * unit_price)()
                data.append(
                    [product_name, str(quantity), f"Rs. {unit_price:.2f}", f"Rs. {subtotal:.2f}"]
                )
                total_for_supplier += subtotal

        if len(data) > 1:
            table = Table(data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 11),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ]
                )
            )
            elements.append(table)

        elements.append(Spacer(1, 6))
        elements.append(
            Paragraph(
                f"<b>Total Amount for {supplier.name}: Rs. {total_for_supplier:.2f}</b>",
                styles["h3"],
            )
        )
        elements.append(Spacer(1, 20))

    doc.build(elements)
    return response


@pharmacist_required
def update_order_status(request, pk):
    """
    Update the status of a purchase order.
    """
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == "POST":
        form = PurchaseOrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order #{order.id} status updated to {order.status}.")
            return redirect("suppliers:order_tracking")
    else:
        form = PurchaseOrderStatusForm(instance=order)

    return render(
        request,
        "supplierManagement/update_order_status.html",
        {"form": form, "order": order},
    )
