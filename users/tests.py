# users/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser", password="testpass123"
        )  # nosec B106
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username="admin", password="adminpass"
        )  # nosec B106
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)


class RemoveExpiredTokensCommandTest(TestCase):
    def test_removes_only_expired_tokens(self):
        old_user = User.objects.create_user(
            username="old", email="old@example.com", password="pass"
        )  # nosec B106
        old_user.date_joined = timezone.now() - timedelta(days=2)
        old_user.save(update_fields=["date_joined"])

        recent_user = User.objects.create_user(
            username="new", email="new@example.com", password="pass"
        )  # nosec B106

        call_command("remove_expired_verification_tokens", days=1)

        old_user.refresh_from_db()
        recent_user.refresh_from_db()

        self.assertIsNone(old_user.verification_token)
        self.assertIsNotNone(recent_user.verification_token)
