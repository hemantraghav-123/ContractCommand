
from django.conf import settings
from django.db import models


class Contract(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        EXPIRED = "EXPIRED", "Expired"
        TERMINATED = "TERMINATED", "Terminated"

    class ContractType(models.TextChoices):
        SUPPLY = "SUPPLY", "Supply"
        SERVICE = "SERVICE", "Service"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        RESEARCH = "RESEARCH", "Research and Development"
        OTHER = "OTHER", "Other"

    contract_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.PROTECT,
        related_name="contracts",
    )

    procurement_plan = models.ForeignKey(
        "procurement.ProcurementPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts",
    )

    contract_type = models.CharField(
        max_length=15,
        choices=ContractType.choices,
        default=ContractType.OTHER,
    )

    contract_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="managed_contracts",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contract_number} - {self.title}"

