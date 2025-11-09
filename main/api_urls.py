from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    UserViewSet, UserAddressViewSet, UserProfileViewSet,
    UserSessionViewSet, UserActivityViewSet, ProductAPIViewSet, CategoryAPIViewSet,
    OrderAPIViewSet, PaymentAPIViewSet, FAQViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'addresses', UserAddressViewSet, basename='address')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'sessions', UserSessionViewSet, basename='session')
router.register(r'activities', UserActivityViewSet, basename='activity')
router.register(r'products', ProductAPIViewSet, basename='product')
router.register(r'categories', CategoryAPIViewSet, basename='category')
router.register(r'orders', OrderAPIViewSet, basename='order')
router.register(r'payments', PaymentAPIViewSet, basename='payment')
router.register(r'faqs', FAQViewSet, basename='faq')

urlpatterns = [
    path('', include(router.urls)),
]

