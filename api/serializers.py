from rest_framework import serializers
from accounts.models import User, VendorProfile
from products.models import Category, Product
from orders.models import Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'is_vendor', 'is_customer', 'avatar_url']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_vendor=validated_data.get('is_vendor', False),
            is_customer=validated_data.get('is_customer', True)
        )
        return user

class VendorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = VendorProfile
        fields = ['id', 'user', 'store_name', 'slug', 'description', 'logo_url', 'banner_url', 'status', 'balance', 'created_at']
        read_only_fields = ['slug', 'status', 'balance', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image_url']
        read_only_fields = ['slug']

class ProductSerializer(serializers.ModelSerializer):
    vendor = serializers.StringRelatedField(read_only=True)
    category_detail = CategorySerializer(source='category', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'vendor', 'category', 'category_detail', 'name', 'slug', 'description', 'price', 'stock', 'image_url', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'vendor', 'created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.store_name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'vendor', 'vendor_name', 'price', 'quantity', 'status']
        read_only_fields = ['price', 'vendor']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'first_name', 'last_name', 'email', 'address', 'city', 'postal_code', 'country', 'total_amount', 'status', 'items', 'created_at']
        read_only_fields = ['customer', 'total_amount', 'status', 'created_at']
