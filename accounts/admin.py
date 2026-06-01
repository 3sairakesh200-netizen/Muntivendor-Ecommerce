from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, VendorProfile

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'is_vendor', 'is_customer', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Roles & Profile', {'fields': ('is_vendor', 'is_customer', 'avatar_url')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Roles & Profile', {'fields': ('is_vendor', 'is_customer', 'avatar_url')}),
    )

admin.site.register(User, CustomUserAdmin)

@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'user', 'status', 'balance', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['store_name', 'user__username', 'user__email']
    prepopulated_fields = {'slug': ('store_name',)}
    actions = ['approve_vendors', 'suspend_vendors']

    def approve_vendors(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_vendors.short_description = "Approve selected vendors"

    def suspend_vendors(self, request, queryset):
        queryset.update(status='SUSPENDED')
    suspend_vendors.short_description = "Suspend selected vendors"
