
import csv
from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render

from contracts.models import Contract
from invoices.models import Invoice
from payments.models import Payment
from procurement.models import ProcurementPlan
from vendors.models import Vendor


def can_view_reports(user):
    return (
        user.is_superuser
        or user.groups.filter(
            name__in=[
                "Administrator",
                "Contract Manager",
                "Procurement Officer",
                "Finance Officer",
            ]
        ).exists()
    )


def require_report_access(user):
    if not can_view_reports(user):
        raise PermissionDenied(
            "You do not have permission to access management reports."
        )


@login_required
def executive_dashboard(request):
    require_report_access(request.user)

    active_contracts = Contract.objects.filter(
        is_archived=False,
        status=Contract.Status.ACTIVE,
    )

    active_plans = ProcurementPlan.objects.filter(
        is_archived=False
    )

    non_rejected_invoices = Invoice.objects.exclude(
        status=Invoice.Status.REJECTED
    )

    completed_payments = Payment.objects.filter(
    status=Payment.Status.COMPLETED,
    invoice__in=non_rejected_invoices,
)

    total_invoiced = non_rejected_invoices.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    total_paid = completed_payments.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    # Calculate outstanding balances per invoice so that an invoice
    # is never shown with a negative outstanding balance.
    payments_by_invoice = defaultdict(lambda: Decimal("0.00"))

    payment_totals = (
        Payment.objects.filter(
            invoice__in=non_rejected_invoices,
            status=Payment.Status.COMPLETED,
        )
        .values("invoice_id")
        .annotate(total=Sum("amount"))
    )

    for item in payment_totals:
        payments_by_invoice[item["invoice_id"]] = item["total"] or Decimal("0.00")

    total_outstanding = Decimal("0.00")

    for invoice in non_rejected_invoices.only("id", "amount"):
        paid_for_invoice = payments_by_invoice[invoice.id]
        total_outstanding += max(
            invoice.amount - paid_for_invoice,
            Decimal("0.00"),
        )

    contract_status_rows = (
        Contract.objects.filter(is_archived=False)
        .values("status")
        .annotate(count=Count("id"), value=Sum("contract_value"))
        .order_by("status")
    )

    procurement_priority_rows = (
        active_plans.values("priority")
        .annotate(count=Count("id"), budget=Sum("estimated_budget"))
        .order_by("priority")
    )

    context = {
        "active_contract_count": active_contracts.count(),
        "contract_count": Contract.objects.filter(
            is_archived=False
        ).count(),
        "procurement_plan_count": active_plans.count(),
        "vendor_count": Vendor.objects.filter(is_active=True).count(),
        "invoice_review_count": Invoice.objects.filter(
            status__in=[
                Invoice.Status.SUBMITTED,
                Invoice.Status.UNDER_REVIEW,
            ]
        ).count(),
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "contract_status_rows": contract_status_rows,
        "procurement_priority_rows": procurement_priority_rows,
    }

    return render(request, "reports/executive_dashboard.html", context)


@login_required
def export_contracts_csv(request):
    require_report_access(request.user)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        'attachment; filename="contractcommand_contracts.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        "Contract Number",
        "Title",
        "Vendor",
        "Contract Type",
        "Contract Value",
        "Start Date",
        "End Date",
        "Status",
    ])

    contracts = Contract.objects.filter(
        is_archived=False
    ).select_related("vendor").order_by("contract_number")

    for contract in contracts.iterator():
        writer.writerow([
            contract.contract_number,
            contract.title,
            contract.vendor.name,
            contract.get_contract_type_display(),
            contract.contract_value,
            contract.start_date,
            contract.end_date,
            contract.get_status_display(),
        ])

    return response


@login_required
def export_invoices_csv(request):
    require_report_access(request.user)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        'attachment; filename="contractcommand_invoices.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        "Invoice Number",
        "Contract Number",
        "Vendor",
        "Invoice Amount",
        "Invoice Date",
        "Due Date",
        "Status",
    ])

    invoices = (
        Invoice.objects.select_related("contract", "contract__vendor")
        .order_by("invoice_number")
    )

    for invoice in invoices.iterator():
        writer.writerow([
            invoice.invoice_number,
            invoice.contract.contract_number,
            invoice.contract.vendor.name,
            invoice.amount,
            invoice.invoice_date,
            invoice.due_date or "",
            invoice.get_status_display(),
        ])

    return response

