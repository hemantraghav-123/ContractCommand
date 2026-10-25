
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class VendorEvaluation(models.Model):
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.PROTECT,
        related_name="evaluations",
    )

    procurement_plan = models.ForeignKey(
        "procurement.ProcurementPlan",
        on_delete=models.PROTECT,
        related_name="vendor_evaluations",
    )

    technical_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    financial_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    delivery_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    compliance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    comments = models.TextField(blank=True)

    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vendor_evaluations",
    )

    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-evaluated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "procurement_plan"],
                name="unique_vendor_evaluation_per_plan",
            )
        ]

    def __str__(self):
        return (
            f"{self.vendor.name} - "
            f"{self.procurement_plan.title}"
        )

