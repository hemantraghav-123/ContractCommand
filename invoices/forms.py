
from django import forms

from contracts.models import Contract

from .models import Invoice


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "invoice_number",
            "contract",
            "amount",
            "invoice_date",
            "due_date",
            "description",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01"}
            ),
            "invoice_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "due_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 4}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contract"].queryset = Contract.objects.filter(
            is_archived=False
        )

    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get("invoice_date")
        due_date = cleaned_data.get("due_date")
        amount = cleaned_data.get("amount")

        if amount is not None and amount <= 0:
            self.add_error("amount", "Invoice amount must be positive.")

        if invoice_date and due_date and due_date < invoice_date:
            self.add_error(
                "due_date",
                "Due date cannot be before the invoice date.",
            )

        return cleaned_data
