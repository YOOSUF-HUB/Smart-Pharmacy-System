from django.shortcuts import redirect, get_object_or_404, render
from django.conf import settings
from django.contrib import messages
import stripe
from prescriptions.models import Prescription, PrescriptionItem
from .models import *
from django.core.paginator import Paginator


stripe.api_key = settings.STRIPE_SECRET_KEY

def checkout_prescription(request, pk):
   
    prescription = get_object_or_404(Prescription, pk=pk)
    
    if not prescription.items.all().exists():
        messages.error(request, "This prescription is empty and cannot be processed for payment.")
        return redirect('prescription_detail', pk=pk)
        
    # --- Create a new Payment object in 'pending' status ---
    payment = Payment.objects.create(
        patient=prescription.patient,
        prescription=prescription,
        status='pending'
    )
    
    # Calculate the total amount and prepare line items for Stripe
    line_items = []
    for item in prescription.items.all():
        unit_amount = int(item.medicine.selling_price * 100)
        
        # --- Create a PaymentItem for each PrescriptionItem ---
        PaymentItem.objects.create(
            payment=payment,
            medicine=item.medicine,
            quantity=item.dispensed_quantity,
            price=item.medicine.selling_price
        )
        
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"{item.medicine.name} ({item.medicine.dosage})",
                },
                'unit_amount': unit_amount,
            },
            'quantity': item.dispensed_quantity,
        })
    
    # Update the payment total
    payment.calculate_total()
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(f'http://127.0.0.1:8000/payments/success/{payment.pk}/'), 
            cancel_url=request.build_absolute_uri(f'http://127.0.0.1:8000/payments/cancelled/{payment.pk}/'),
            metadata={'payment_id': payment.id},
        )
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        messages.error(request, f"An error occurred while creating the checkout session: {str(e)}")
        # If an error occurs, delete the pending payment and its items
        payment.delete()
        return redirect('prescription_detail', pk=pk)

def success_payment(request, pk):
    """
    Handles successful payment from Stripe.
    Updates the Payment object's status and shows a success message.
    """
    payment = get_object_or_404(Payment, pk=pk)
    payment.status = 'paid'
    payment.save()
    
    messages.success(request, f"Payment #{payment.id} for Prescription #{payment.prescription.id} was successful!")
    
    return redirect('payment_detail', pk=payment.pk)

def cancel_payment(request, pk):
    """
    Handles cancelled payment from Stripe.
    Deletes the Payment object and redirects to the payment list page.
    """
    payment = get_object_or_404(Payment, pk=pk)
    # The payment was cancelled, so we delete the pending record
    payment.delete()
    
    messages.info(request, "Payment was cancelled. You can try again.")
    return redirect('payment_list')

def payment_list(request):
    """
    Displays a paginated list of all payments.
    """
    payments = Payment.objects.all().order_by('-payment_date')
    
    # Set up pagination
    paginator = Paginator(payments, 10) # Show 10 payments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'payments/payment_list.html', context)

def payment_detail(request, pk):
    """
    Displays the details of a single payment.
    """
    payment = get_object_or_404(Payment, pk=pk)
    context = {
        'payment': payment,
        'payment_items': payment.payment_items.all(),
    }
    return render(request, 'payments/payment_detail.html', context)

