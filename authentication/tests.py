from django.test import TestCase
from django.contrib.auth import get_user_model

class UserModelTest(TestCase):
    def test_create_user(self):
        user = get_user_model().objects.create_user(username='testuser', password='testpass123')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
