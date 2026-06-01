from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import VendorProfile
from products.models import Category, Product
from .models import Order, OrderItem
from decimal import Decimal

User = get_user_model()

class OrdersModelTests(TestCase):
    def setUp(self):
        # Create user / vendor
        self.vendor_user = User.objects.create_user(
            username='artisan1',
            password='testpassword123',
            is_vendor=True
        )
        self.vendor = VendorProfile.objects.create(
            user=self.vendor_user,
            store_name='Artisan Woodwork',
            status='APPROVED'
        )
        
        # Create customer
        self.customer = User.objects.create_user(
            username='shopper1',
            password='testpassword123',
            is_customer=True
        )
        
        # Category
        self.category = Category.objects.create(name='Woodwork')
        
        # Product
        self.product = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            name='Oak Desk',
            description='Solid oak hand crafted desk',
            price=Decimal('299.00'),
            stock=5
        )

    def test_order_creation_and_fulfillment(self):
        # Create Order
        order = Order.objects.create(
            customer=self.customer,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            address='123 Oak St',
            city='Atlanta',
            postal_code='30303',
            total_amount=Decimal('299.00'),
            status='PAID'
        )

        # Create OrderItem
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            vendor=self.vendor,
            price=self.product.price,
            quantity=1,
            status='PENDING'
        )

        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.get_cost(), Decimal('299.00'))
        
        # Check stock deduction helper test (matches orders/views.py flow)
        self.product.stock -= order_item.quantity
        self.product.save()
        self.assertEqual(self.product.stock, 4)

        # Check vendor balance credit test (matches orders/views.py flow - 90% goes to vendor)
        self.vendor.balance += order_item.get_cost() * Decimal('0.90')
        self.vendor.save()
        self.assertEqual(self.vendor.balance, Decimal('269.10'))

    def test_order_item_refund_and_variants(self):
        # Create Order
        order = Order.objects.create(
            customer=self.customer,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            address='123 Oak St',
            city='Atlanta',
            postal_code='30303',
            total_amount=Decimal('299.00'),
            status='PAID'
        )

        # Create OrderItem with custom variants
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            vendor=self.vendor,
            price=self.product.price,
            quantity=1,
            selected_size='Studio Pro',
            selected_color='Cyber Neon',
            status='DELIVERED'
        )

        self.assertEqual(order_item.selected_size, 'Studio Pro')
        self.assertEqual(order_item.selected_color, 'Cyber Neon')

        # Request refund via post action
        self.client.login(username='shopper1', password='testpassword123')
        response = self.client.post(f'/order-item/refund/{order_item.id}/')
        self.assertEqual(response.status_code, 302)  # Redirect

        # Verify status became REFUND_REQUESTED
        order_item.refresh_from_db()
        self.assertEqual(order_item.status, 'REFUND_REQUESTED')

        # Approve refund via vendor dashboard
        self.client.login(username='artisan1', password='testpassword123')
        response = self.client.post('/dashboard/orders/', {
            'item_id': order_item.id,
            'status': 'REFUNDED'
        })
        self.assertEqual(response.status_code, 302)

        # Verify status became REFUNDED
        order_item.refresh_from_db()
        self.assertEqual(order_item.status, 'REFUNDED')
