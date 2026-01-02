from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from products.models import Category, Product
from reviews.models import Review


@override_settings(SECURE_SSL_REDIRECT=False)
class ReviewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="reviewer", password="pass"  # nosec B106
        )
        self.admin = user_model.objects.create_superuser(
            username="admin", password="pass"  # nosec B106
        )
        self.category = Category.objects.create(name="Skincare")
        self.product = Product.objects.create(
            product_name="Sample Lotion",
            category=self.category,
            price="19.99",
            inventory=10,
        )
        self.client = APIClient()
        self.list_url = reverse("review-list", kwargs={"version": "v1"})

    def test_authenticated_user_creates_pending_review(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.list_url,
            {
                "product_id": self.product.id,
                "rating": 5,
                "title": "Great",
                "body": "Loved it",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        review = Review.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.status, Review.Status.PENDING)
        self.product.refresh_from_db()
        self.assertEqual(self.product.average_rating, Decimal("0.00"))
        self.assertEqual(self.product.rating_count, 0)

    def test_duplicate_review_rejected(self):
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
        )
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.list_url,
            {"product_id": self.product.id, "rating": 5},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_approves_review_and_rating_updates(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
        )
        self.client.force_authenticate(self.admin)
        detail_url = reverse(
            "review-detail", kwargs={"version": "v1", "pk": review.id}
        )
        response = self.client.patch(
            detail_url, {"status": "approved"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.average_rating, Decimal("4.00"))
        self.assertEqual(self.product.rating_count, 1)

    def test_public_list_shows_only_approved(self):
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            status=Review.Status.PENDING,
        )
        Review.objects.create(
            product=self.product,
            user=self.admin,
            rating=3,
            status=Review.Status.APPROVED,
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
