import logging
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ForgotPasswordForm,
    UserRegistrationForm,
    VerifyCodeAndSignInForm,
)
from .models import EmailVerificationCode

logger = logging.getLogger(__name__)
User = get_user_model()


def ensure_default_roles():
    """Ensure standard defense contract role groups exist."""
    roles = [
        "Administrator",
        "Contract Manager",
        "Procurement Officer",
        "Finance Officer",
    ]
    for role in roles:
        Group.objects.get_or_create(name=role)


@login_required
def dashboard(request):
    role_names = list(
        request.user.groups.values_list("name", flat=True)
    )

    if request.user.is_superuser:
        role = "Administrator"
    elif role_names:
        role = ", ".join(role_names)
    else:
        role = "No role assigned"

    return render(
        request,
        "accounts/dashboard.html",
        {
            "role": role,
            "username": request.user.username,
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    is_first_user = User.objects.count() == 0

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])

            ensure_default_roles()

            if is_first_user:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                admin_group, _ = Group.objects.get_or_create(name="Administrator")
                admin_group.user_set.add(user)
                messages.success(
                    request,
                    "Account created successfully! As the first user, you have been granted Administrator privileges.",
                )
            else:
                user.save()
                messages.success(
                    request,
                    f"Welcome to ContractCommand, {user.username}! Your account has been registered.",
                )

            login(request, user)
            return redirect("dashboard")
    else:
        form = UserRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "is_first_user": is_first_user,
        },
    )


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            user = form.user

            # Invalidate any active previous codes for this user
            EmailVerificationCode.objects.filter(user=user, is_used=False).update(is_used=True)

            # Generate secure 6-digit numeric OTP code
            code = f"{secrets.randbelow(900000) + 100000}"
            EmailVerificationCode.objects.create(user=user, code=code)

            request.session["reset_user_id"] = user.id

            # Compose verification email
            subject = "ContractCommand - Sign-in & Password Reset Verification Code"
            recipient_name = user.get_full_name() or user.username
            message = (
                f"Hello {recipient_name},\n\n"
                f"A sign-in code was requested for your ContractCommand account.\n\n"
                f"Your 6-digit verification code is: {code}\n\n"
                f"This code is valid for 15 minutes. Enter this code to sign in and reset your password.\n\n"
                f"If you did not request this code, you can safely ignore this email.\n\n"
                f"— ContractCommand Security"
            )

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                masked_email = (
                    user.email[:2] + "***@" + user.email.split("@")[1]
                    if "@" in user.email
                    else user.email
                )
                if not getattr(settings, "EMAIL_HOST_USER", None) or "console" in getattr(settings, "EMAIL_BACKEND", ""):
                    messages.info(
                        request,
                        f"SMTP email is not yet configured in your Render environment variables. Your 6-digit code is: {code} (Also printed in Render server logs).",
                    )
                else:
                    messages.success(
                        request,
                        f"Verification code sent to {masked_email}. Please check your email inbox.",
                    )
            except Exception as e:
                logger.error("Failed to send verification code email: %s", e)
                # Show helpful notification in case SMTP credentials are not yet configured on Render
                messages.warning(
                    request,
                    f"Verification code generated ({code}). (Email error: {e}. If testing without SMTP, check server logs.)",
                )

            return redirect("verify_code")
    else:
        form = ForgotPasswordForm()

    return render(
        request,
        "accounts/forgot_password.html",
        {"form": form},
    )


def verify_code(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    user_id = request.session.get("reset_user_id")
    if not user_id:
        messages.info(
            request,
            "Please enter your username or email address first to receive a verification code.",
        )
        return redirect("forgot_password")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = VerifyCodeAndSignInForm(request.POST)
        if form.is_valid():
            code_input = form.cleaned_data["code"].strip()
            verification = EmailVerificationCode.objects.filter(
                user=user, code=code_input, is_used=False
            ).first()

            if verification and verification.is_valid():
                verification.is_used = True
                verification.save(update_fields=["is_used"])

                new_password = form.cleaned_data.get("new_password")
                if new_password:
                    user.set_password(new_password)
                    user.save()
                    messages.success(
                        request,
                        "Your password has been updated and you are now signed in!",
                    )
                else:
                    messages.success(
                        request,
                        "Signed in successfully with your verification code!",
                    )

                login(request, user)
                request.session.pop("reset_user_id", None)
                return redirect("dashboard")
            else:
                form.add_error(
                    "code",
                    "Invalid or expired verification code. Please check your code or request a new one.",
                )
    else:
        form = VerifyCodeAndSignInForm()

    masked_email = (
        user.email[:2] + "***@" + user.email.split("@")[1]
        if "@" in user.email
        else user.email
    )

    return render(
        request,
        "accounts/verify_code.html",
        {
            "form": form,
            "masked_email": masked_email,
            "username": user.username,
        },
    )
