# orders/tests.py

from django.test import TestCase
from orders.models import Order, OrderItem
from mongoengine import connect, disconnect
import mongomock
from django.contrib.auth import get_user_model

class OrderModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Connect to a test database (in-memory or separate)
        connect('mongoenginetest', host='mongodb://localhost', mongo_client_class=mongomock.MongoClient)

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='u', password='p')
        self.order = Order.objects.create(
            user=self.user,
            total_price=100.0,
            shipping_cost=10.0,
            tax_amount=5.0,
            status='pending',
            created_at="2025-01-01T12:00:00Z"
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product_name="Soap",
            quantity=2,
            unit_price=50.0
        )

    def test_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.items.count(), 1)
        self.assertEqual(self.order.items.first().product_name, "Soap")
        self.assertEqual(self.order.status, 'pending')
