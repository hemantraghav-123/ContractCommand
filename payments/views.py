
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from invoices.models import Invoice

from .forms import PaymentForm
from .models import Payment


def can_manage_payments(user):
    return (
        user.is_superuser
        or user.groups.filter(
            name__in=["Administrator", "Finance Officer"]
        ).exists()
    )


def require_payment_manager(user):
    if not can_manage_payments(user):
        raise PermissionDenied(
            "You do not have permission to manage payments."
        )


def refresh_invoice_status(invoice):
    paid_total = invoice.payment_set.filter(
        status=Payment.Status.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    if paid_total >= invoice.amount:
        invoice.status = Invoice.Status.PAID
    elif paid_total > 0:
        invoice.status = Invoice.Status.PARTIALLY_PAID
    else:
        invoice.status = Invoice.Status.APPROVED

    invoice.save(update_fields=["status"])


@login_required
def payment_list(request):
    require_payment_manager(request.user)

    payments = Payment.objects.select_related(
        "invoice", "invoice__contract"
    ).order_by("-created_at")

    return render(
        request,
        "payments/payment_list.html",
        {"payments": payments},
    )


@login_required
def payment_create(request):
    require_payment_manager(request.user)

    if request.method == "POST":
        form = PaymentForm(request.POST)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.status = Payment.Status.PENDING
            payment.save()

            messages.success(
                request,
                "Payment recorded as pending. Confirm it only after "
                "the payment has actually been made.",
            )
            return redirect("payments:list")
    else:
        form = PaymentForm()

    return render(
        request,
        "payments/payment_form.html",
        {"form": form, "page_title": "Record Payment"},
    )


@login_required
@require_POST
def payment_complete(request, pk):
    require_payment_manager(request.user)

    with transaction.atomic():
        payment = get_object_or_404(
            Payment.objects.select_related("invoice"),
            pk=pk,
        )

        invoice = Invoice.objects.select_for_update().get(
            pk=payment.invoice_id
        )

        # Reload the payment after locking the invoice row.
        payment = Payment.objects.get(pk=pk)

        if payment.status != Payment.Status.PENDING:
            messages.error(
                request,
                "Only pending payments can be marked completed.",
            )
            return redirect("payments:list")

        paid_so_far = Payment.objects.filter(
            invoice=invoice,
            status=Payment.Status.COMPLETED,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        if paid_so_far + payment.amount > invoice.amount:
            messages.error(
                request,
                "This payment would exceed the remaining invoice balance.",
            )
            return redirect("payments:list")

        payment.status = Payment.Status.COMPLETED
        payment.save(update_fields=["status"])

        refresh_invoice_status(invoice)

    messages.success(request, "Payment marked as completed.")
    return redirect("payments:list")

