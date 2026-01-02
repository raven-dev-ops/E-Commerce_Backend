from threading import Barrier, Thread

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from giftcards.models import GiftCard


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver"])
class GiftCardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin", password="pass", is_staff=True
        )  # nosec B106
        self.user = User.objects.create_user(
            username="giftuser", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)
        self.list_url = reverse("giftcard-list", kwargs={"version": "v1"})
        self.redeem_url = reverse("giftcard-redeem", kwargs={"version": "v1"})

    def test_admin_can_issue_giftcard(self):
        response = self.admin_client.post(
            self.list_url, {"amount": "25.00"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        card = GiftCard.objects.get(id=response.data["id"])
        self.assertEqual(card.issued_by, self.admin)

    def test_non_admin_cannot_issue_giftcard(self):
        response = self.client.post(self.list_url, {"amount": "25.00"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_non_admin_cannot_list_giftcards(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 403)

    def test_redeem_giftcard(self):
        card = GiftCard.objects.create(amount=10, balance=10, issued_by=self.admin)
        response = self.client.post(self.redeem_url, {"code": card.code}, format="json")
        self.assertEqual(response.status_code, 200)
        card.refresh_from_db()
        self.assertFalse(card.is_active)
        self.assertEqual(card.balance, 0)
        self.assertEqual(card.redeemed_by, self.user)


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver"])
class GiftCardConcurrencyTests(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="concurrentuser", password="pass"
        )  # nosec B106
        self.card = GiftCard.objects.create(amount=10, balance=10)
        self.redeem_url = reverse("giftcard-redeem", kwargs={"version": "v1"})

    def _redeem(self, barrier, results, index):
        client = APIClient()
        client.force_authenticate(self.user)
        barrier.wait()
        response = client.post(self.redeem_url, {"code": self.card.code}, format="json")
        results[index] = response.status_code

    def test_concurrent_redeem_only_one_succeeds(self):
        if connection.vendor == "sqlite":
            self.skipTest("SQLite does not support concurrent write tests.")
        barrier = Barrier(2)
        results = [None, None]
        threads = [
            Thread(target=self._redeem, args=(barrier, results, i)) for i in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sorted(results), [200, 404])
        self.card.refresh_from_db()
        self.assertFalse(self.card.is_active)
        self.assertEqual(self.card.balance, 0)
