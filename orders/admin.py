from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product', 'vendor']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'first_name', 'last_name', 'email', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['first_name', 'last_name', 'email', 'address']
    inlines = [OrderItemInline]
    list_editable = ['status']
