
from django import forms

from .models import Vendor


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            "vendor_code",
            "name",
            "category",
            "country",
            "contact_person",
            "email",
            "phone",
            "address",
            "qualification_status",
            "is_active",
        ]

        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "email": forms.EmailInput(),
        }
