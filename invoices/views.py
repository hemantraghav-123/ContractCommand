
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InvoiceForm
from .models import Invoice


def can_manage_finance(user):
    return (
        user.is_superuser
        or user.groups.filter(
            name__in=["Administrator", "Finance Officer"]
        ).exists()
    )


def can_submit_invoices(user):
    return (
        can_manage_finance(user)
        or user.groups.filter(name="Contract Manager").exists()
    )


def require_finance(user):
    if not can_manage_finance(user):
        raise PermissionDenied(
            "You do not have permission to perform this financial action."
        )


@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related("contract").all()

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query)
            | Q(contract__contract_number__icontains=query)
            | Q(contract__title__icontains=query)
            | Q(contract__vendor__name__icontains=query)
        )

    valid_statuses = {
        value for value, label in Invoice.Status.choices
    }

    if status in valid_statuses:
        invoices = invoices.filter(status=status)
    else:
        status = ""

    total_invoiced = invoices.exclude(
        status=Invoice.Status.REJECTED
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    return render(
        request,
        "invoices/invoice_list.html",
        {
            "invoices": invoices,
            "query": query,
            "selected_status": status,
            "status_choices": Invoice.Status.choices,
            "total_invoiced": total_invoiced,
            "can_submit": can_submit_invoices(request.user),
            "can_manage_finance": can_manage_finance(request.user),
        },
    )


@login_required
def invoice_create(request):
    if not can_submit_invoices(request.user):
        raise PermissionDenied(
            "You do not have permission to submit invoices."
        )

    if request.method == "POST":
        form = InvoiceForm(request.POST)

        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.status = Invoice.Status.SUBMITTED
            invoice.save()

            messages.success(request, "Invoice submitted successfully.")
            return redirect("invoices:detail", pk=invoice.pk)
    else:
        form = InvoiceForm()

    return render(
        request,
        "invoices/invoice_form.html",
        {"form": form, "page_title": "Submit Invoice"},
    )


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "contract", "contract__vendor"
        ),
        pk=pk,
    )

    payments = invoice.payment_set.all().order_by("-created_at")
    paid_total = payments.filter(
        status="COMPLETED"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    balance = max(invoice.amount - paid_total, Decimal("0.00"))

    return render(
        request,
        "invoices/invoice_detail.html",
        {
            "invoice": invoice,
            "payments": payments,
            "paid_total": paid_total,
            "balance": balance,
            "can_manage_finance": can_manage_finance(request.user),
            "can_submit": can_submit_invoices(request.user),
        },
    )


@login_required
@require_POST
def invoice_action(request, pk, action):
    require_finance(request.user)

    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status not in [
        Invoice.Status.SUBMITTED,
        Invoice.Status.UNDER_REVIEW,
    ]:
        messages.error(
            request,
            "Only submitted or under-review invoices can be reviewed.",
        )
        return redirect("invoices:detail", pk=invoice.pk)

    if action == "review":
        invoice.status = Invoice.Status.UNDER_REVIEW
        message = "Invoice marked as under review."
    elif action == "approve":
        invoice.status = Invoice.Status.APPROVED
        message = "Invoice approved."
    elif action == "reject":
        invoice.status = Invoice.Status.REJECTED
        message = "Invoice rejected."
    else:
        raise PermissionDenied("Unsupported invoice action.")

    invoice.save(update_fields=["status"])
    messages.success(request, message)
    return redirect("invoices:detail", pk=invoice.pk)

