from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Order, OrderItem

# compute field names at module level so class-body comprehensions can access them
ORDER_FIELD_NAMES = {f.name for f in Order._meta.get_fields()}


# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 
        'product_type', 
        'available_online', 
        'featured', 
        'price', 
        'stock'  
    )
    list_filter = ('product_type', 'available_online', 'featured')
    search_fields = ('medicine__name', 'non_medical_product__name')
    
    # These are your model's helper methods
    @admin.display(description='Price')
    def price(self, obj):
        return obj.price

    @admin.display(description='Stock')
    def stock(self, obj):
        return obj.stock

# --- Orders admin below ---

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_link', 'price', 'quantity', 'subtotal')
    fields = ('product_link', 'price', 'quantity', 'subtotal')
    can_delete = False

    def product_link(self, obj):
        prod = getattr(obj, 'product', None)
        if prod:
            try:
                url = prod.get_absolute_url()
            except Exception:
                url = '#'
            return format_html('<a href="{}" target="_blank">{}</a>', url, prod)
        return '-'
    product_link.short_description = 'Product'

    def subtotal(self, obj):
        try:
            return (getattr(obj, 'quantity', 0) or 0) * (getattr(obj, 'price', 0) or 0)
        except Exception:
            return '-'
    subtotal.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Build sensible list_display based on available fields
    list_display = []
    if 'id' in ORDER_FIELD_NAMES:
        list_display.append('id')
    # fallback to __str__ if no id present
    if not list_display:
        list_display = ['__str__']

    if 'user' in ORDER_FIELD_NAMES:
        list_display.append('user')
    if 'status' in ORDER_FIELD_NAMES:
        list_display.append('status')

    list_display.append('total_amount')  # method below always present

    if 'created_at' in ORDER_FIELD_NAMES:
        list_display.append('created_at')
    if 'updated_at' in ORDER_FIELD_NAMES:
        list_display.append('updated_at')

    list_filter = tuple(f for f in ('status', 'created_at') if f in ORDER_FIELD_NAMES)
    search_fields = tuple(
        f for f in ('id', 'user__email', 'user__username') if (f.split('__')[0] in ORDER_FIELD_NAMES)
    )
    readonly_fields = tuple(f for f in ('created_at', 'updated_at') if f in ORDER_FIELD_NAMES)
    inlines = [OrderItemInline]
    ordering = ('-created_at',) if 'created_at' in ORDER_FIELD_NAMES else ('-pk',)
    list_per_page = 25

    def total_amount(self, obj):
        # try common fields/methods
        for candidate in ('total', 'amount', 'get_total', 'get_amount'):
            if hasattr(obj, candidate):
                attr = getattr(obj, candidate)
                try:
                    return attr() if callable(attr) else attr
                except Exception:
                    continue
        # fallback: sum related items
        for rel in ('items', 'order_items', 'orderitem_set'):
            if hasattr(obj, rel):
                try:
                    rel_qs = getattr(obj, rel).all()
                    return sum((getattr(i, 'quantity', 0) * getattr(i, 'price', 0) for i in rel_qs))
                except Exception:
                    continue
        return '-'
    total_amount.short_description = 'Total'