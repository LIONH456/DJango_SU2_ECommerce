from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import SliderViewSet

router = DefaultRouter()
router.register(r'sliders', SliderViewSet, basename='slider')

urlpatterns = [
    path('', include(router.urls)),
]

