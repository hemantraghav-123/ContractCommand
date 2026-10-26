
from django import forms

from .models import ProcurementPlan


class ProcurementPlanForm(forms.ModelForm):
    class Meta:
        model = ProcurementPlan
        fields = [
            "title",
            "requirement_description",
            "department",
            "estimated_budget",
            "expected_date",
            "priority",
            "status",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "e.g. Radar Maintenance Equipment"}
            ),
            "requirement_description": forms.Textarea(
                attrs={"rows": 4}
            ),
            "department": forms.TextInput(
                attrs={"placeholder": "e.g. Engineering"}
            ),
            "estimated_budget": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01"}
            ),
            "expected_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def clean_estimated_budget(self):
        budget = self.cleaned_data["estimated_budget"]

        if budget <= 0:
            raise forms.ValidationError(
                "Estimated budget must be greater than zero."
            )

        return budget
