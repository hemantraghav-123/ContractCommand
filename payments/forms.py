
from django import forms

from invoices.models import Invoice

from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "invoice",
            "reference",
            "amount",
            "payment_date",
            "notes",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01"}
            ),
            "payment_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "notes": forms.Textarea(
                attrs={"rows": 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Payments can be recorded only against approved,
        # not-yet-fully-paid invoices.
        self.fields["invoice"].queryset = Invoice.objects.filter(
            status__in=[
                Invoice.Status.APPROVED,
                Invoice.Status.PARTIALLY_PAID,
            ]
        )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]

        if amount <= 0:
            raise forms.ValidationError(
                "Payment amount must be greater than zero."
            )

        return amount
