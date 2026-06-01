from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('vendor/register/', views.vendor_register_view, name='vendor_register'),
    
    # Customer Dashboard & Actions
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('address/create/', views.address_create, name='address_create'),
    path('address/delete/<int:pk>/', views.address_delete, name='address_delete'),
    path('address/default/<int:pk>/', views.address_set_default, name='address_set_default'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('notification/read/<int:pk>/', views.notification_read, name='notification_read'),
]
