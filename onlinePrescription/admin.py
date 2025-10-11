# ...existing code...
from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe

from .models import Prescription


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "nic", "status", "uploaded_at", "order_link", "preview")
    list_filter = ("status", "uploaded_at")
    search_fields = ("user__username", "user__email", "nic")
    readonly_fields = ("uploaded_at", "preview")
    ordering = ("-uploaded_at",)
    actions = ("mark_reviewed", "approve_prescriptions", "reject_prescriptions")
    list_per_page = 25

    fieldsets = (
        (None, {"fields": ("user", "prescription_image", "preview", "notes", "nic", "order")}),
        ("Workflow", {"fields": ("status", "pharmacist_comment", "uploaded_at")}),
    )

    def preview(self, obj):
        if obj.prescription_image:
            return mark_safe(f'<img src="{obj.prescription_image.url}" style="max-height:150px; max-width:250px;" />')
        return "-"
    preview.short_description = "Image preview"

    def order_link(self, obj):
        if obj.order:
            url = reverse(
                "admin:%s_%s_change" % (obj.order._meta.app_label, obj.order._meta.model_name),
                args=(obj.order.pk,),
            )
            return mark_safe(f'<a href="{url}">Order #{obj.order.order_id}</a>')
        return "-"
    order_link.short_description = "Order"

    # Admin actions
    def mark_reviewed(self, request, queryset):
        updated = queryset.update(status="Reviewed")
        self.message_user(request, f"{updated} prescription(s) marked as Reviewed.")
    mark_reviewed.short_description = "Mark selected prescriptions as Reviewed"

    def approve_prescriptions(self, request, queryset):
        updated = queryset.update(status="Approved")
        self.message_user(request, f"{updated} prescription(s) approved.")
    approve_prescriptions.short_description = "Approve selected prescriptions"

    def reject_prescriptions(self, request, queryset):
        updated = queryset.update(status="Rejected")
        self.message_user(request, f"{updated} prescription(s) rejected.")
    reject_prescriptions.short_description = "Reject selected prescriptions"
# ...existing code...