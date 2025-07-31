from django.test import TestCase
from mongoengine import connect, disconnect
import mongomock

from discounts.models import Discount
from products.models import Product, Category


class DiscountModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connect('mongoenginetest', host='mongodb://localhost', mongo_client_class=mongomock.MongoClient)

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        Discount.drop_collection()
        Product.drop_collection()
        Category.drop_collection()
        self.category = Category.objects.create(name='TestCat')
        self.discount = Discount.objects.create(
            code='SAVE10',
            discount_type='percentage',
            value=10,
            is_active=True,
            category=self.category
        )

    def test_discount_str(self):
        self.assertEqual(str(self.discount), 'SAVE10 (percentage)')

    def test_discount_defaults(self):
        self.assertEqual(self.discount.times_used, 0)
        self.assertTrue(self.discount.is_active)
