from django.contrib import admin
from .models import EmailVerificationCode


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "is_used")
    list_filter = ("is_used", "created_at")
    search_fields = ("user__username", "user__email", "code")
