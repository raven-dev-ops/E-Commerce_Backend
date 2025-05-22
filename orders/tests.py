# orders/tests.py

from django.test import TestCase
from orders.models import Order, OrderItem
from mongoengine import connect, disconnect

class OrderModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Connect to a test database (in-memory or separate)
        connect('mongoenginetest', host='mongomock://localhost')

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        # Create sample OrderItem
        self.order_item = OrderItem(product_id="507f1f77bcf86cd799439011", quantity=2)

        # Create sample Order
        self.order = Order(
            user=1,
            total_price=100.0,
            shipping_cost=10.0,
            tax_amount=5.0,
            status='pending',
            items=[self.order_item],
            created_at="2025-01-01T12:00:00Z"
        )
        self.order.save()

    def test_order_creation(self):
        self.assertEqual(self.order.user, 1)
        self.assertEqual(len(self.order.items), 1)
        self.assertEqual(self.order.items[0].product_id, "507f1f77bcf86cd799439011")
        self.assertEqual(self.order.status, 'pending')
