from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "placeholder": "Create a secure password"}
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "placeholder": "Re-enter your password"}
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "e.g. jdoe"}),
            "email": forms.EmailInput(attrs={"placeholder": "e.g. jdoe@example.com"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First name (optional)"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name (optional)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error("confirm_password", "Passwords do not match.")
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error("password", e)

        return cleaned_data


class ForgotPasswordForm(forms.Form):
    identifier = forms.CharField(
        label="Username or Email Address",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "placeholder": "Enter your username or registered email",
            }
        ),
    )

    def clean_identifier(self):
        identifier = self.cleaned_data["identifier"].strip()
        user = (
            User.objects.filter(username__iexact=identifier).first()
            or User.objects.filter(email__iexact=identifier).first()
        )

        if not user:
            raise ValidationError("No registered account found with that username or email.")

        if not user.email:
            raise ValidationError(
                "This account does not have an email address associated with it. Please contact an administrator."
            )

        if not user.is_active:
            raise ValidationError("This account is currently disabled. Please contact an administrator.")

        self.user = user
        return identifier


class VerifyCodeAndSignInForm(forms.Form):
    code = forms.CharField(
        label="6-Digit Verification Code",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "placeholder": "123456",
                "maxlength": "6",
                "pattern": "[0-9]{6}",
                "style": "letter-spacing: 6px; font-size: 22px; text-align: center; font-weight: bold;",
            }
        ),
    )
    new_password = forms.CharField(
        label="New Password (Optional)",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Leave blank to just sign in, or set a new password",
            }
        ),
        help_text="Optional: Enter a new password if you want to reset your forgotten password.",
    )
    confirm_new_password = forms.CharField(
        label="Confirm New Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Re-enter your new password",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if new_password or confirm_new_password:
            if new_password != confirm_new_password:
                self.add_error("confirm_new_password", "Passwords do not match.")
            elif new_password:
                try:
                    validate_password(new_password)
                except ValidationError as e:
                    self.add_error("new_password", e)

        return cleaned_data
