from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from backend.currency import convert_amount, get_exchange_rate


class CurrencyTests(SimpleTestCase):
    @patch("backend.currency.requests.get")
    def test_get_exchange_rate_returns_decimal(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"rates": {"EUR": 1.2345}}
        mock_get.return_value = mock_response

        rate = get_exchange_rate("usd", "eur")

        self.assertEqual(rate, Decimal("1.2345"))

    @patch("backend.currency.get_exchange_rate")
    def test_convert_amount_rounds_half_up(self, mock_rate):
        mock_rate.return_value = Decimal("1")

        result = convert_amount(Decimal("10.005"), "USD", "EUR")

        self.assertEqual(result, Decimal("10.01"))
