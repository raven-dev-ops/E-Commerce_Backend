from django.test import SimpleTestCase, override_settings
from django.urls import reverse


@override_settings(SECURE_SSL_REDIRECT=False)
class MetricsEndpointTests(SimpleTestCase):
    def test_metrics_disabled_returns_404(self):
        url = reverse("metrics")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(METRICS_AUTH_TOKEN="secret", METRICS_ALLOWED_IPS=[])
    def test_metrics_requires_token(self):
        url = reverse("metrics")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response = self.client.get(url, HTTP_X_METRICS_TOKEN="secret")
        self.assertEqual(response.status_code, 200)

    @override_settings(METRICS_AUTH_TOKEN="", METRICS_ALLOWED_IPS=["127.0.0.1"])
    def test_metrics_allows_ip(self):
        url = reverse("metrics")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
