from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # Home pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_details, name='blog_details'),
    path('contact/', views.contact, name='contact'),
    path('elements/', views.elements, name='elements'),
    
    # Store pages
    path('shop/', views.shop, name='shop'),
    path('product/<str:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment, name='payment'),
    path('order/thanks/', views.order_thanks, name='order_thanks'),
    path('order/<str:order_id>/', views.order_detail, name='order_detail'),
    path('api/cancel-order/', views.cancel_order, name='cancel_order'),


    
    # Authentication pages
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/profile/', views.profile_view, name='profile'),
    path('auth/logout/', views.logout_view, name='logout'),
    # Cart and Address API endpoints
    path('api/save-cart/', views.save_cart, name='save_cart'),
    path('api/load-cart/', views.load_cart, name='load_cart'),
    path('api/save-address/', views.save_address, name='save_address'),
    path('api/get-addresses/', views.get_addresses, name='get_addresses'),
    path('api/get-address/<str:address_id>/', views.get_address, name='get_address'),
    path('api/update-address/', views.update_address_mongo, name='update_address_mongo'),
    path('api/delete-address/', views.delete_address_mongo, name='delete_address_mongo'),
    # Wishlist API endpoints
    path('api/add-wishlist/', views.add_wishlist, name='add_wishlist'),
    path('api/remove-wishlist/', views.remove_wishlist, name='remove_wishlist'),
    path('api/load-wishlist/', views.load_wishlist, name='load_wishlist'),
    # Order API endpoints
    path('api/create-order/', views.create_order, name='create_order'),
    path('api/generate-bakong-qr/', views.generate_bakong_qr, name='generate_bakong_qr'),
    path('api/check-payment-status/', views.check_payment_status, name='check_payment_status'),
    # PayPal API endpoints
    path('api/paypal/create/', views.paypal_create_order, name='paypal_create_order'),
    path('api/paypal/capture/', views.paypal_capture_order, name='paypal_capture_order'),
    path('payment/paypal/return/', views.paypal_return, name='paypal_return'),
    path('payment/paypal/cancel/', views.paypal_cancel, name='paypal_cancel'),
]
