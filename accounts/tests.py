from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from .models import EmailVerificationCode

User = get_user_model()


class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_first_user_becomes_administrator(self):
        """The first registered user must be granted Administrator privileges."""
        self.assertEqual(User.objects.count(), 0)

        response = self.client.post(
            reverse("register"),
            {
                "username": "adminuser",
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="adminuser")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.groups.filter(name="Administrator").exists())

    def test_subsequent_user_is_standard_user(self):
        """Subsequent users created after the first are standard users."""
        User.objects.create_superuser(
            username="initialadmin",
            email="initial@example.com",
            password="StrongPassword123!",
        )

        response = self.client.post(
            reverse("register"),
            {
                "username": "regularuser",
                "email": "regular@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="regularuser")
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_forgot_password_and_code_sign_in(self):
        """Requesting forgot password sends a 6-digit code which can be used to sign in."""
        user = User.objects.create_user(
            username="johndoe",
            email="john@example.com",
            password="OldPassword123!",
        )

        # 1. Request forgot password
        response = self.client.post(
            reverse("forgot_password"),
            {"identifier": "johndoe"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("verify_code"))

        # Check that email was sent with 6-digit code
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("6-digit verification code", mail.outbox[0].body)

        verification = EmailVerificationCode.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(verification)
        self.assertEqual(len(verification.code), 6)

        # 2. Verify code and sign in with new password
        verify_response = self.client.post(
            reverse("verify_code"),
            {
                "code": verification.code,
                "new_password": "NewSecurePassword456!",
                "confirm_new_password": "NewSecurePassword456!",
            },
        )
        self.assertEqual(verify_response.status_code, 302)
        self.assertRedirects(verify_response, reverse("dashboard"))

        # Verify password was updated
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewSecurePassword456!"))

        # Code is now marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)

    def test_invalid_verification_code_rejected(self):
        """An invalid verification code must not sign the user in."""
        user = User.objects.create_user(
            username="janedoe",
            email="jane@example.com",
            password="Password123!",
        )

        self.client.post(
            reverse("forgot_password"),
            {"identifier": "jane@example.com"},
        )

        response = self.client.post(
            reverse("verify_code"),
            {"code": "000000"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid or expired verification code")
