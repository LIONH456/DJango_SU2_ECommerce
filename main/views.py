from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.contrib.auth import get_user_model

User = get_user_model()
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .mongodb_utils import mongodb_manager
import json

# Import the Slider model from dashboard app
from dashboard.models import Slider

def home(request):
    """Home page view"""
    # Fetch active sliders from database, ordered by their order field
    sliders = Slider.objects.filter(status='active').order_by('order')
    
    context = {
        'page_title': 'Home',
        'sliders': sliders,
        'featured_products': [],  # Add featured products logic here
        'new_arrivals': [],       # Add new arrivals logic here
        'popular_products': [],   # Add popular products logic here
    }
    return render(request, 'Home/index.html', context)

def about(request):
    """About page view"""
    context = {
        'page_title': 'About Us',
        'team_members': [
            {
                'name': 'John Doe',
                'position': 'Creative Director',
                'image': 'assets/img/gallery/team1.png'
            },
            {
                'name': 'Jane Smith',
                'position': 'Fashion Designer',
                'image': 'assets/img/gallery/team2.png'
            },
            {
                'name': 'Mike Johnson',
                'position': 'Marketing Manager',
                'image': 'assets/img/gallery/team3.png'
            }
        ]
    }
    return render(request, 'Home/about.html', context)

def blog(request):
    """Blog listing page view"""
    context = {
        'page_title': 'Blog',
        'blog_posts': [],  # Add blog posts logic here
        'blog_categories': [],  # Add categories logic here
        'recent_posts': [],  # Add recent posts logic here
        'popular_tags': [],  # Add tags logic here
    }
    return render(request, 'Home/blog.html', context)

def blog_details(request, slug):
    """Blog detail page view"""
    context = {
        'page_title': 'Blog Post',
        'post': None,  # Add blog post logic here
        'related_posts': [],  # Add related posts logic here
    }
    return render(request, 'Home/blog_details.html', context)

def contact(request):
    """Contact page view"""
    if request.method == 'POST':
        # Handle contact form submission
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically save to database or send email
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('main:contact')
    
    context = {
        'page_title': 'Contact Us',
    }
    return render(request, 'Home/contact.html', context)

def elements(request):
    """Elements page view"""
    context = {
        'page_title': 'Elements',
    }
    return render(request, 'Home/elements.html', context)

def shop(request):
    """Shop/Product listing page view"""
    context = {
        'page_title': 'Shop',
        'products': [],  # Add products logic here
        'categories': [],  # Add categories logic here
    }
    return render(request, 'store/product_list.html', context)

def product_detail(request, product_id):
    """Product detail page view"""
    context = {
        'page_title': 'Product Detail',
        'product': None,  # Add product logic here
        'related_products': [],  # Add related products logic here
    }
    return render(request, 'store/product_detail.html', context)

def cart(request):
    """Shopping cart page view"""
    context = {
        'page_title': 'Shopping Cart',
        'cart_items': [],  # Add cart items logic here
        'cart_subtotal': 0,
        'cart_total': 0,
        'shipping_cost': 0,
        'tax_amount': 0,
        'recommended_products': [],  # Add recommended products logic here
    }
    return render(request, 'store/cart.html', context)

# Authentication views
def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    context = {
        'page_title': 'Login',
    }
    return render(request, 'auth/login.html', context)

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('main:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Validation
        errors = []
        
        # Check if username already exists
        if mongodb_manager.get_user_by_username(username):
            errors.append('Username already exists.')
        
        # Check if email already exists
        if mongodb_manager.get_user_by_email(email):
            errors.append('Email already exists.')
        
        # Check password match
        if password1 != password2:
            errors.append('Passwords do not match.')
        
        # Check password length
        if len(password1) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        # Check if username is valid
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        # Check if email is valid
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if not errors:
            try:
                # Create user data
                user_data = {
                    'username': username,
                    'email': email,
                    'password': password1,  # Will be hashed automatically
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': request.POST.get('phone', ''),
                    'date_of_birth': request.POST.get('date_of_birth', ''),
                    'newsletter': request.POST.get('newsletter') == 'on',
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False
                }
                
                # Create user in MongoDB
                user_id = mongodb_manager.create_user(user_data)
                
                if user_id:
                    # Authenticate and login the user
                    user = authenticate(request, username=username, password=password1)
                    if user:
                        login(request, user)
                        messages.success(request, f'Account created successfully! Welcome, {username}!')
                        return redirect('dashboard:dashboard')
                    else:
                        messages.error(request, 'Account created but login failed. Please try logging in.')
                        return redirect('main:login')
                else:
                    messages.error(request, 'Failed to create account. Please try again.')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            for error in errors:
                messages.error(request, error)
    
    context = {
        'page_title': 'Register',
    }
    return render(request, 'auth/register.html', context)

@login_required
def profile_view(request):
    """User profile view"""
    context = {
        'page_title': 'Profile',
        'orders': [],  # Add user orders logic here
        'wishlist_items': [],  # Add wishlist logic here
        'addresses': [],  # Add addresses logic here
    }
    return render(request, 'auth/profile.html', context)

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('main:home')

# API views for AJAX requests
@csrf_exempt
def add_to_cart(request):
    """Add product to cart via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            # Add to cart logic here
            
            return JsonResponse({'success': True, 'message': 'Product added to cart'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid data'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def update_cart(request):
    """Update cart items via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            updates = data.get('updates', [])
            
            # Update cart logic here
            
            return JsonResponse({'success': True, 'message': 'Cart updated successfully'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid data'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def remove_from_cart(request):
    """Remove item from cart via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            # Remove from cart logic here
            
            return JsonResponse({'success': True, 'message': 'Item removed from cart'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid data'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def clear_cart(request):
    """Clear entire cart via AJAX"""
    if request.method == 'POST':
        # Clear cart logic here
        
        return JsonResponse({'success': True, 'message': 'Cart cleared successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


