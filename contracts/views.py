
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ContractForm
from .models import Contract


def can_manage_contracts(user):
    return (
        user.is_superuser
        or user.groups.filter(
            name__in=["Administrator", "Contract Manager"]
        ).exists()
    )


def require_contract_manager(user):
    if not can_manage_contracts(user):
        raise PermissionDenied(
            "You do not have permission to manage contracts."
        )


@login_required
def contract_list(request):
    contracts = Contract.objects.filter(is_archived=False).select_related(
        "vendor", "managed_by", "procurement_plan"
    )

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if query:
        contracts = contracts.filter(
            Q(contract_number__icontains=query)
            | Q(title__icontains=query)
            | Q(vendor__name__icontains=query)
        )

    valid_statuses = {choice[0] for choice in Contract.Status.choices}

    if status in valid_statuses:
        contracts = contracts.filter(status=status)
    else:
        status = ""

    return render(
        request,
        "contracts/contract_list.html",
        {
            "contracts": contracts,
            "query": query,
            "selected_status": status,
            "status_choices": Contract.Status.choices,
            "can_manage": can_manage_contracts(request.user),
        },
    )


@login_required
def contract_create(request):
    require_contract_manager(request.user)

    if request.method == "POST":
        form = ContractForm(request.POST)

        if form.is_valid():
            contract = form.save(commit=False)
            contract.managed_by = request.user
            contract.save()

            messages.success(
                request,
                "Contract created successfully.",
            )
            return redirect("contracts:detail", pk=contract.pk)
    else:
        form = ContractForm()

    return render(
        request,
        "contracts/contract_form.html",
        {"form": form, "page_title": "Create Contract"},
    )


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related(
            "vendor", "managed_by", "procurement_plan"
        ),
        pk=pk,
    )

    return render(
        request,
        "contracts/contract_detail.html",
        {
            "contract": contract,
            "can_manage": can_manage_contracts(request.user),
        },
    )


@login_required
def contract_update(request, pk):
    require_contract_manager(request.user)

    contract = get_object_or_404(
        Contract,
        pk=pk,
        is_archived=False,
    )

    if request.method == "POST":
        form = ContractForm(request.POST, instance=contract)

        if form.is_valid():
            updated_contract = form.save(commit=False)

            # Preserve the original responsible manager.
            updated_contract.managed_by = contract.managed_by
            updated_contract.save()

            messages.success(
                request,
                "Contract updated successfully.",
            )
            return redirect(
                "contracts:detail",
                pk=updated_contract.pk,
            )
    else:
        form = ContractForm(instance=contract)

    return render(
        request,
        "contracts/contract_form.html",
        {"form": form, "page_title": "Edit Contract"},
    )


@login_required
@require_POST
def contract_archive(request, pk):
    require_contract_manager(request.user)

    contract = get_object_or_404(
        Contract,
        pk=pk,
        is_archived=False,
    )

    contract.is_archived = True
    contract.save(update_fields=["is_archived", "updated_at"])

    messages.success(request, "Contract archived successfully.")
    return redirect("contracts:list")

