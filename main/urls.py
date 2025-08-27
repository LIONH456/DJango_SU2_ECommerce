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


    
    # Authentication pages
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/profile/', views.profile_view, name='profile'),
    path('auth/logout/', views.logout_view, name='logout'),
    

]
