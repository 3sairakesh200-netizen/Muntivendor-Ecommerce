from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Sum, Q
from accounts.models import User, VendorProfile
from products.models import Category, Product
from orders.models import Order, OrderItem
from .serializers import (
    UserSerializer, VendorProfileSerializer, CategorySerializer,
    ProductSerializer, OrderSerializer, OrderItemSerializer
)
from decimal import Decimal

# Custom Permission to check if the user is the owning vendor of the product
class IsVendorOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_vendor and hasattr(request.user, 'vendor_profile')

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.vendor == request.user.vendor_profile

class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # If user registered as vendor, create their VendorProfile
        if user.is_vendor:
            store_name = request.data.get('store_name')
            description = request.data.get('description', '')
            if not store_name:
                user.delete()
                return Response(
                    {"error": "Store name is required when registering as a vendor."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            VendorProfile.objects.create(
                user=user,
                store_name=store_name,
                description=description,
                status='APPROVED' # Auto-approved for simple workspace testing
            )
            
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

class VendorProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VendorProfile.objects.filter(status='APPROVED')
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('vendor', 'category')
    serializer_class = ProductSerializer
    permission_classes = [IsVendorOwnerOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search query
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
            
        # Category filter
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        # Vendor filter
        vendor_slug = self.request.query_params.get('vendor')
        if vendor_slug:
            queryset = queryset.filter(vendor__slug=vendor_slug)
            
        return queryset

    def perform_create(self, serializer):
        # Associate product with the active vendor profile
        serializer.save(vendor=self.request.user.vendor_profile)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Customers see only their own orders
        return Order.objects.filter(customer=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        # Advanced API order placement with atomic transactions and stock checks
        cart_items_data = request.data.get('items', [])
        if not cart_items_data:
            return Response(
                {"error": "Please provide items to checkout."},
                status=status.HTTP_400_BAD_REQUEST
            )

        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        address = request.data.get('address')
        city = request.data.get('city')
        postal_code = request.data.get('postal_code')
        country = request.data.get('country', 'United States')

        if not all([first_name, last_name, email, address, city, postal_code]):
            return Response(
                {"error": "Missing billing / shipping address fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    customer=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address=address,
                    city=city,
                    postal_code=postal_code,
                    country=country,
                    total_amount=Decimal('0.00'), # Will update below
                    status='PAID'
                )

                total_amount = Decimal('0.00')

                for item_data in cart_items_data:
                    product_id = item_data.get('product')
                    quantity = int(item_data.get('quantity', 1))
                    
                    product = get_object_or_404(Product, id=product_id, is_active=True)
                    
                    if product.stock < quantity:
                        raise ValueError(f"Insufficient stock for product '{product.name}'. Available: {product.stock}")
                    
                    # Deduct stock
                    product.stock -= quantity
                    product.save()

                    item_cost = product.price * quantity
                    total_amount += item_cost

                    # Create OrderItem
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        vendor=product.vendor,
                        price=product.price,
                        quantity=quantity,
                        status='PENDING'
                    )

                    # Credit Vendor Account
                    product.vendor.balance += item_cost * Decimal('0.90')
                    product.vendor.save()

                order.total_amount = total_amount
                order.save()

                serializer = self.get_serializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An error occurred during payment processing."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VendorDashboardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_vendor or not hasattr(request.user, 'vendor_profile'):
            return Response({"error": "Unauthorized. Vendor credentials required."}, status=status.HTTP_403_FORBIDDEN)

        vendor = request.user.vendor_profile
        products = Product.objects.filter(vendor=vendor)
        order_items = OrderItem.objects.filter(vendor=vendor)

        # Totals
        total_earnings = sum(item.price * item.quantity for item in order_items.filter(order__status='PAID'))
        total_orders = order_items.values('order').distinct().count()
        total_products = products.count()
        unfulfilled = order_items.exclude(status='DELIVERED').count()

        # Detailed item list
        items_serializer = OrderItemSerializer(order_items, many=True)

        return Response({
            "store_name": vendor.store_name,
            "balance": vendor.balance,
            "status": vendor.status,
            "metrics": {
                "total_earnings": total_earnings,
                "total_orders": total_orders,
                "total_products": total_products,
                "pending_fulfillments": unfulfilled
            },
            "recent_orders": items_serializer.data
        })
