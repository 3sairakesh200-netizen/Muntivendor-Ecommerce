from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Custom Applications Routing
    path('', include('accounts.urls')),
    path('', include('products.urls')),
    path('', include('orders.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/v1/', include('api.urls')),
]
