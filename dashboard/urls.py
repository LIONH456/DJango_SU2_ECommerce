from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('sliders/', views.sliders_list, name='sliders_list'),
    path('sliders/create/', views.slider_create, name='slider_create'),
    path('sliders/<int:slider_id>/edit/', views.slider_edit, name='slider_edit'),
    path('sliders/<int:slider_id>/delete/', views.slider_delete, name='slider_delete'),
    path('sliders/<int:slider_id>/toggle-status/', views.slider_toggle_status, name='slider_toggle_status'),
    path('sliders/reorder/', views.slider_reorder, name='slider_reorder'),
    # Product Management
    path('products/', views.products_list, name='products_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<str:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<str:product_id>/delete/', views.product_delete, name='product_delete'),
    # Category Management
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<str:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<str:category_id>/delete/', views.category_delete, name='category_delete'),
    # Order Management
    path('orders/', views.orders_list, name='orders_list'),
    # Payment Management
    path('payments/', views.payments_list, name='payments_list'),
    # User Management
    path('users/', views.users_list, name='users_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<str:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<str:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
]