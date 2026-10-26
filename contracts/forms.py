
from django import forms

from .models import Contract


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            "contract_number",
            "title",
            "description",
            "vendor",
            "procurement_plan",
            "contract_type",
            "contract_value",
            "start_date",
            "end_date",
            "status",
        ]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "contract_value": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01"}
            ),
            "start_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["procurement_plan"].queryset = (
    self.fields["procurement_plan"].queryset.filter(
        is_archived=False
    )
)

        self.fields["procurement_plan"].required = False

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "End date cannot be before start date.",
            )

        return cleaned_data
