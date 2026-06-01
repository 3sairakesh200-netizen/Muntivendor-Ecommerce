from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='api_category')
router.register('vendors', views.VendorProfileViewSet, basename='api_vendor')
router.register('products', views.ProductViewSet, basename='api_product')
router.register('orders', views.OrderViewSet, basename='api_order')

urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),
    
    # Custom JWT & Auth Endpoint mappings
    path('auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Custom Vendor Dashboard analytic monitors
    path('vendor/dashboard/', views.VendorDashboardAPIView.as_view(), name='api_vendor_dashboard'),
]
