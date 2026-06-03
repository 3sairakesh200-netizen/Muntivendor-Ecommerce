from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_page, name='terms'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
]
