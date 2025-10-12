from celery import shared_task
from django.conf import settings
from django.utils import timezone
from pathlib import Path
from .models import Medicine  # adjust import

@shared_task
def export_medicines_pdf_task(filters: dict | None = None) -> str:
    # Apply filters as needed
    qs = Medicine.objects.all()
    # Example filters (extend as needed)
    name_q = (filters or {}).get("q")
    if name_q:
        qs = qs.filter(name__icontains=name_q)

    # Only needed fields; iterate in chunks
    qs = qs.values_list("id", "name", "brand", "selling_price", "stock").order_by("name")

    # Prepare output path
    ts = timezone.now().strftime("%Y%m%d-%H%M%S")
    rel_path = f"exports/medicines-{ts}.pdf"
    out_path = Path(settings.MEDIA_ROOT) / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate PDF quickly with ReportLab
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4

    left = 15 * mm
    top = height - 20 * mm
    y = top

    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "Medicine Inventory Export")
    y -= 10 * mm

    # Header
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "No")
    c.drawString(left + 15*mm, y, "Name")
    c.drawString(left + 95*mm, y, "Brand")
    c.drawString(left + 135*mm, y, "Price")
    c.drawString(left + 160*mm, y, "Stock")
    y -= 6 * mm
    c.line(left, y+2*mm, width - 15*mm, y+2*mm)

    c.setFont("Helvetica", 9)
    line_height = 5.2 * mm
    row = 0

    for i, (mid, name, brand, price, stock) in enumerate(qs.iterator(chunk_size=1000), start=1):
        if y < 20 * mm:
            c.showPage()
            y = top
            c.setFont("Helvetica", 9)

        # Truncate long text to keep layout fast/small
        name_txt = (name or "")[:60]
        brand_txt = (brand or "")[:24]

        c.drawString(left, y, str(i))
        c.drawString(left + 15*mm, y, name_txt)
        c.drawString(left + 95*mm, y, brand_txt)
        c.drawRightString(left + 155*mm, y, f"Rs {price}")
        c.drawRightString(left + 185*mm, y, str(stock if stock is not None else 0))
        y -= line_height
        row += 1

    c.save()
    return f"{settings.MEDIA_URL}{rel_path}"