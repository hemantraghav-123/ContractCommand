
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import VendorForm
from .models import Vendor


def can_manage_vendors(user):
    return (
        user.is_superuser
        or user.groups.filter(
            name__in=["Administrator", "Procurement Officer"]
        ).exists()
    )


def require_vendor_manager(user):
    if not can_manage_vendors(user):
        raise PermissionDenied(
            "You do not have permission to manage vendors."
        )


@login_required
def vendor_list(request):
    vendors = Vendor.objects.all()

    query = request.GET.get("q", "").strip()
    qualification = request.GET.get("qualification", "").strip()
    active = request.GET.get("active", "").strip()

    if query:
        vendors = vendors.filter(
            Q(vendor_code__icontains=query)
            | Q(name__icontains=query)
            | Q(category__icontains=query)
            | Q(country__icontains=query)
        )

    valid_qualifications = {
        value for value, label in Vendor.QualificationStatus.choices
    }

    if qualification in valid_qualifications:
        vendors = vendors.filter(
            qualification_status=qualification
        )
    else:
        qualification = ""

    if active == "yes":
        vendors = vendors.filter(is_active=True)
    elif active == "no":
        vendors = vendors.filter(is_active=False)
    else:
        active = ""

    return render(
        request,
        "vendors/vendor_list.html",
        {
            "vendors": vendors,
            "query": query,
            "selected_qualification": qualification,
            "selected_active": active,
            "qualification_choices": Vendor.QualificationStatus.choices,
            "can_manage": can_manage_vendors(request.user),
        },
    )


@login_required
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)

    return render(
        request,
        "vendors/vendor_detail.html",
        {
            "vendor": vendor,
            "can_manage": can_manage_vendors(request.user),
        },
    )


@login_required
def vendor_create(request):
    require_vendor_manager(request.user)

    if request.method == "POST":
        form = VendorForm(request.POST)

        if form.is_valid():
            vendor = form.save()
            messages.success(
                request, "Vendor registered successfully."
            )
            return redirect("vendors:detail", pk=vendor.pk)
    else:
        form = VendorForm()

    return render(
        request,
        "vendors/vendor_form.html",
        {"form": form, "page_title": "Register Vendor"},
    )


@login_required
def vendor_update(request, pk):
    require_vendor_manager(request.user)
    vendor = get_object_or_404(Vendor, pk=pk)

    if request.method == "POST":
        form = VendorForm(request.POST, instance=vendor)

        if form.is_valid():
            vendor = form.save()
            messages.success(
                request, "Vendor updated successfully."
            )
            return redirect("vendors:detail", pk=vendor.pk)
    else:
        form = VendorForm(instance=vendor)

    return render(
        request,
        "vendors/vendor_form.html",
        {"form": form, "page_title": "Edit Vendor"},
    )


@login_required
@require_POST
def vendor_deactivate(request, pk):
    require_vendor_manager(request.user)

    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.is_active = False
    vendor.save(update_fields=["is_active"])

    messages.success(request, "Vendor deactivated successfully.")
    return redirect("vendors:detail", pk=vendor.pk)

