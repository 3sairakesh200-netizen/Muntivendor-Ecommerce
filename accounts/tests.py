from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import VendorProfile

User = get_user_model()

class AccountsModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='buyer1',
            email='buyer1@example.com',
            password='testpassword123',
            is_customer=True,
            is_vendor=False
        )
        self.assertEqual(user.username, 'buyer1')
        self.assertTrue(user.is_customer)
        self.assertFalse(user.is_vendor)
        self.assertEqual(str(user), 'buyer1')

    def test_create_vendor_profile(self):
        user = User.objects.create_user(
            username='merchant1',
            email='merchant1@example.com',
            password='testpassword123',
            is_customer=False,
            is_vendor=True
        )
        vendor = VendorProfile.objects.create(
            user=user,
            store_name='Artisan Goods',
            description='Handcrafted with care'
        )
        self.assertEqual(vendor.store_name, 'Artisan Goods')
        self.assertEqual(vendor.slug, 'artisan-goods')
        self.assertEqual(vendor.status, 'PENDING')
        self.assertEqual(str(vendor), 'Artisan Goods')
