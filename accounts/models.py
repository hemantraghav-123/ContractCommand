import datetime
from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_codes",
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Email Verification Code"
        verbose_name_plural = "Email Verification Codes"

    def is_valid(self):
        """Valid for 15 minutes and only if not previously used."""
        return (not self.is_used) and (
            timezone.now() - self.created_at
        ) < datetime.timedelta(minutes=15)

    def __str__(self):
        status = "Used" if self.is_used else ("Valid" if self.is_valid() else "Expired")
        return f"{self.user.username} - {self.code} ({status})"
