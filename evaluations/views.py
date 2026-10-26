
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from procurement.models import ProcurementPlan
from vendors.models import Vendor

from .forms import VendorEvaluationForm
from .models import VendorEvaluation


def can_manage_evaluations(user):
    return (
        user.is_superuser
        or user.groups.filter(
            name__in=["Administrator", "Procurement Officer"]
        ).exists()
    )


def require_evaluation_manager(user):
    if not can_manage_evaluations(user):
        raise PermissionDenied(
            "You do not have permission to manage evaluations."
        )


def weighted_score(evaluation):
    return (
        evaluation.technical_score * Decimal("0.40")
        + evaluation.financial_score * Decimal("0.25")
        + evaluation.delivery_score * Decimal("0.20")
        + evaluation.compliance_score * Decimal("0.15")
    ).quantize(Decimal("0.01"))


@login_required
def evaluation_list(request):
    evaluations = VendorEvaluation.objects.select_related(
        "vendor", "procurement_plan", "evaluated_by"
    )

    plan_id = request.GET.get("plan", "").strip()
    if plan_id.isdigit():
        evaluations = evaluations.filter(
            procurement_plan_id=int(plan_id)
        )
    else:
        plan_id = ""

    rows = [
        {
            "evaluation": evaluation,
            "score": weighted_score(evaluation),
        }
        for evaluation in evaluations
    ]
    rows.sort(key=lambda row: row["score"], reverse=True)

    plans = ProcurementPlan.objects.filter(is_archived=False)

    return render(
        request,
        "evaluations/evaluation_list.html",
        {
            "rows": rows,
            "plans": plans,
            "selected_plan": plan_id,
            "can_manage": can_manage_evaluations(request.user),
        },
    )


@login_required
def evaluation_create(request):
    require_evaluation_manager(request.user)

    initial = {}
    plan_id = request.GET.get("plan", "").strip()

    if plan_id.isdigit():
        if ProcurementPlan.objects.filter(
            pk=int(plan_id), is_archived=False
        ).exists():
            initial["procurement_plan"] = int(plan_id)

    if request.method == "POST":
        form = VendorEvaluationForm(request.POST)

        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.evaluated_by = request.user
            evaluation.save()

            messages.success(
                request, "Vendor evaluation saved successfully."
            )
            return redirect("evaluations:list")
    else:
        form = VendorEvaluationForm(initial=initial)

    return render(
        request,
        "evaluations/evaluation_form.html",
        {"form": form, "page_title": "Evaluate Vendor"},
    )


@login_required
def evaluation_compare(request, plan_id):
    plan = get_object_or_404(
        ProcurementPlan,
        pk=plan_id,
        is_archived=False,
    )

    evaluations = VendorEvaluation.objects.filter(
        procurement_plan=plan
    ).select_related("vendor", "evaluated_by")

    rows = [
        {
            "evaluation": evaluation,
            "score": weighted_score(evaluation),
        }
        for evaluation in evaluations
    ]
    rows.sort(key=lambda row: row["score"], reverse=True)

    return render(
        request,
        "evaluations/evaluation_compare.html",
        {
            "plan": plan,
            "rows": rows,
        },
    )
