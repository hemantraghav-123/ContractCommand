
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProcurementPlanForm
from .models import ProcurementPlan


def can_manage_procurement(user):
    return (
        user.is_superuser
        or user.groups.filter(
            name__in=["Administrator", "Procurement Officer"]
        ).exists()
    )


def require_procurement_manager(user):
    if not can_manage_procurement(user):
        raise PermissionDenied(
            "You do not have permission to manage procurement plans."
        )


@login_required
def procurement_list(request):
    plans = ProcurementPlan.objects.filter(
        is_archived=False
    ).select_related("created_by")

    query = request.GET.get("q", "").strip()
    priority = request.GET.get("priority", "").strip()
    status = request.GET.get("status", "").strip()

    if query:
        plans = plans.filter(
            Q(title__icontains=query)
            | Q(department__icontains=query)
            | Q(requirement_description__icontains=query)
        )

    valid_priorities = {
        value for value, label in ProcurementPlan.Priority.choices
    }
    valid_statuses = {
        value for value, label in ProcurementPlan.Status.choices
    }

    if priority in valid_priorities:
        plans = plans.filter(priority=priority)
    else:
        priority = ""

    if status in valid_statuses:
        plans = plans.filter(status=status)
    else:
        status = ""

    total_budget = plans.aggregate(
        total=Sum("estimated_budget")
    )["total"] or Decimal("0.00")

    return render(
        request,
        "procurement/procurement_list.html",
        {
            "plans": plans,
            "query": query,
            "selected_priority": priority,
            "selected_status": status,
            "priority_choices": ProcurementPlan.Priority.choices,
            "status_choices": ProcurementPlan.Status.choices,
            "total_budget": total_budget,
            "can_manage": can_manage_procurement(request.user),
        },
    )


@login_required
def procurement_detail(request, pk):
    plan = get_object_or_404(
        ProcurementPlan.objects.select_related("created_by"),
        pk=pk,
        is_archived=False,
    )

    return render(
        request,
        "procurement/procurement_detail.html",
        {
            "plan": plan,
            "can_manage": can_manage_procurement(request.user),
        },
    )


@login_required
def procurement_create(request):
    require_procurement_manager(request.user)

    if request.method == "POST":
        form = ProcurementPlanForm(request.POST)

        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            plan.save()

            messages.success(
                request, "Procurement plan created successfully."
            )
            return redirect("procurement:detail", pk=plan.pk)
    else:
        form = ProcurementPlanForm()

    return render(
        request,
        "procurement/procurement_form.html",
        {"form": form, "page_title": "Create Procurement Plan"},
    )


@login_required
def procurement_update(request, pk):
    require_procurement_manager(request.user)

    plan = get_object_or_404(
        ProcurementPlan,
        pk=pk,
        is_archived=False,
    )

    if request.method == "POST":
        form = ProcurementPlanForm(request.POST, instance=plan)

        if form.is_valid():
            form.save()
            messages.success(
                request, "Procurement plan updated successfully."
            )
            return redirect("procurement:detail", pk=plan.pk)
    else:
        form = ProcurementPlanForm(instance=plan)

    return render(
        request,
        "procurement/procurement_form.html",
        {"form": form, "page_title": "Edit Procurement Plan"},
    )


@login_required
@require_POST
def procurement_archive(request, pk):
    require_procurement_manager(request.user)

    plan = get_object_or_404(
        ProcurementPlan,
        pk=pk,
        is_archived=False,
    )

    plan.is_archived = True
    plan.save(update_fields=["is_archived"])

    messages.success(request, "Procurement plan archived successfully.")
    return redirect("procurement:list")
