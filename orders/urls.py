from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.order_create, name='checkout'),
    path('checkout/coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('checkout/coupon/remove/', views.remove_coupon, name='remove_coupon'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('order-item/refund/<int:item_id>/', views.order_item_refund, name='order_item_refund'),
]
