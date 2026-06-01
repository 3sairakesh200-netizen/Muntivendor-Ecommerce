from django.test import TestCase
from accounts.models import User, VendorProfile
from .models import Category, Product, Review

class ProductsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='vendor1',
            email='vendor1@example.com',
            password='testpassword123',
            is_vendor=True
        )
        self.vendor = VendorProfile.objects.create(
            user=self.user,
            store_name='Vendor One'
        )
        self.category = Category.objects.create(
            name='Electronics',
            description='Tech items'
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Electronics')
        self.assertEqual(self.category.slug, 'electronics')

    def test_product_creation(self):
        product = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            name='Wireless Headphones',
            description='Premium noise cancelling',
            price=199.99,
            stock=15
        )
        self.assertEqual(product.name, 'Wireless Headphones')
        self.assertEqual(product.slug, 'wireless-headphones')
        self.assertEqual(product.stock, 15)
        self.assertEqual(str(product), 'Wireless Headphones')

    def test_review_creation(self):
        product = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            name='Wireless Headphones',
            description='Premium noise cancelling',
            price=199.99,
            stock=15
        )
        review = Review.objects.create(
            product=product,
            user=self.user,
            rating=5,
            comment='Excellent sound!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent sound!')
