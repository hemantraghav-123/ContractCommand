
from django import forms

from procurement.models import ProcurementPlan
from vendors.models import Vendor

from .models import VendorEvaluation


class VendorEvaluationForm(forms.ModelForm):
    class Meta:
        model = VendorEvaluation
        fields = [
            "vendor",
            "procurement_plan",
            "technical_score",
            "financial_score",
            "delivery_score",
            "compliance_score",
            "comments",
        ]

        widgets = {
            "technical_score": forms.NumberInput(
                attrs={"min": "0", "max": "100", "step": "0.01"}
            ),
            "financial_score": forms.NumberInput(
                attrs={"min": "0", "max": "100", "step": "0.01"}
            ),
            "delivery_score": forms.NumberInput(
                attrs={"min": "0", "max": "100", "step": "0.01"}
            ),
            "compliance_score": forms.NumberInput(
                attrs={"min": "0", "max": "100", "step": "0.01"}
            ),
            "comments": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["vendor"].queryset = Vendor.objects.filter(
            is_active=True
        )

        self.fields["procurement_plan"].queryset = (
            ProcurementPlan.objects.filter(is_archived=False)
        )

    def clean(self):
        cleaned_data = super().clean()
        vendor = cleaned_data.get("vendor")
        plan = cleaned_data.get("procurement_plan")

        if vendor and plan:
            existing = VendorEvaluation.objects.filter(
                vendor=vendor,
                procurement_plan=plan,
            )

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    "This vendor already has an evaluation for this "
                    "procurement plan. Open the existing evaluation "
                    "instead of creating a duplicate."
                )

        return cleaned_data
