from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import time
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
import logging
logger = logging.getLogger(__name__)

# Import Telegram notification utilities
from .telegram_utils import send_order_notification, send_payment_notification


def send_html_email(subject, template_name, context, to_email):
    """Render an HTML email and send with a plain-text fallback."""
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    send_mail(
        subject,
        text_content,
        getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        [to_email],
        html_message=html_content,
        fail_silently=False,
    )

from django.contrib.auth import get_user_model

User = get_user_model()
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .mongodb_utils import mongodb_manager
import json
import os

# Import the Slider model from dashboard app
from dashboard.models import Slider

def home(request):
    """Home page view - using MongoDB for sliders"""
    # Fetch active sliders from MongoDB
    try:
        sliders_data = mongodb_manager.list_sliders(status='active')
        # Convert MongoDB data to a format compatible with template
        # Template expects objects with .title, .subtitle, .img, .link, etc.
        class SliderObject:
            def __init__(self, data):
                self.id = data.get('id')
                self.title = data.get('title', '')
                self.subtitle = data.get('subtitle', '')
                self.description = data.get('description', '')
                self.img = data.get('img', '')
                self.link = data.get('link', '')
                self.status = data.get('status', 'active')
                self.order = data.get('order', 0)
        
        sliders = [SliderObject(s) for s in sliders_data] if sliders_data else []
    except Exception as e:
        logger.exception(f"Error fetching sliders from MongoDB: {e}")
        # Fallback to Django ORM if MongoDB fails
        try:
            sliders = Slider.objects.filter(status='active').order_by('order')
        except Exception:
            sliders = []
    
    # Fetch last 4 products for new arrivals via API
    try:
        from .api_client import get_api_client
        api_client = get_api_client(request, use_api=True)
        new_arrivals = api_client.get_new_arrivals(limit=4)
    except Exception:
        # Fallback to direct access
        new_arrivals = mongodb_manager.list_products(
            sort_by='newest',
            page=1,
            page_size=4
        )['items']
    
    context = {
        'page_title': 'Home',
        'sliders': sliders,
        'featured_products': [],  # Add featured products logic here
        'new_arrivals': new_arrivals,
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
    """Shop/Product listing page view (MongoDB)"""
    category = request.GET.get('category')
    search = request.GET.get('q')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort')
    
    # Get initial 21 products for infinite scroll
    result = mongodb_manager.list_products(
        category=category, 
        search=search, 
        max_price=max_price,
        sort_by=sort_by,
        page=1, 
        page_size=1000  # Load all products at once
    )

    # Fetch all active categories from MongoDB
    try:
        all_categories = mongodb_manager.list_categories(is_active=True)
        # Build hierarchical category structure
        categories_tree = []
        category_map = {}
        
        # First pass: create map of all categories
        for cat in all_categories:
            category_map[cat['id']] = cat
            cat['children'] = []
        
        # Second pass: build tree structure
        for cat in all_categories:
            if cat.get('parent_id') and cat['parent_id'] in category_map:
                # This is a child category
                category_map[cat['parent_id']]['children'].append(cat)
            else:
                # This is a top-level category
                categories_tree.append(cat)
        
        # Sort categories by sort_order
        def sort_categories(cats):
            cats.sort(key=lambda x: x.get('sort_order', 0))
            for cat in cats:
                if cat['children']:
                    sort_categories(cat['children'])
        
        sort_categories(categories_tree)
    except Exception as e:
        logger.exception(f"Error fetching categories: {e}")
        categories_tree = []

    context = {
        'page_title': 'Shop',
        'products': result['items'],
        'total_products': result['total'],
        'categories': categories_tree,
        'current_category': category or '',
        'search_query': search or '',
    }
    return render(request, 'store/product_list.html', context)





def product_detail(request, product_id):
    """Product detail page view (MongoDB)"""
    product = mongodb_manager.get_product_by_id(str(product_id))
    if not product:
        return render(request, 'store/product_detail.html', {
            'page_title': 'Product not found',
            'product': None,
            'related_products': [],
            'is_in_wishlist': False,
        })

    # naive related products: same category if present
    related = []
    if product.get('category_id'):
        # Convert category_id to string if it's an ObjectId
        category_id = product['category_id']
        if not isinstance(category_id, str):
            category_id = str(category_id)
        rel_result = mongodb_manager.list_products(category=category_id, page=1, page_size=4)
        related = [p for p in rel_result['items'] if p['id'] != product['id']][:4]

    # Check if product is in user's wishlist
    is_in_wishlist = False
    if request.user.is_authenticated:
        try:
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if mongo_user:
                user_id = str(mongo_user.get('_id'))
                is_in_wishlist = mongodb_manager.is_in_wishlist(user_id, product_id)
        except:
            pass

    context = {
        'page_title': product['name'],
        'product': product,
        'related_products': related,
        'is_in_wishlist': is_in_wishlist,
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
        # Redirect superusers to dashboard, normal users to home
        if request.user.is_superuser:
            return redirect('dashboard:dashboard')
        else:
            return redirect('main:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            # Redirect superusers to dashboard, normal users to home
            if user.is_superuser:
                return redirect('dashboard:dashboard')
            else:
                return redirect('main:home')
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
                        # Redirect normal users to home, admin users to dashboard
                        if user.is_superuser:
                            return redirect('dashboard:dashboard')
                        else:
                            return redirect('main:home')
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
    """User profile view with full CRUD operations"""
    from .models import UserAddress, UserProfile
    
    # Handle POST requests
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            try:
                # Update Django User model
                user = request.user
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.email = request.POST.get('email', '')
                if hasattr(user, 'phone'):
                    user.phone = request.POST.get('phone', '')
                user.save()
                
                # Update or create UserProfile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.bio = request.POST.get('bio', '')
                profile.phone = request.POST.get('phone', '')
                
                # Handle avatar upload
                if 'avatar' in request.FILES:
                    avatar_file = request.FILES['avatar']
                    # Create avatars directory if it doesn't exist
                    if settings.STATICFILES_DIRS:
                        static_root = settings.STATICFILES_DIRS[0]
                    elif hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                        static_root = settings.STATIC_ROOT
                    else:
                        static_root = os.path.join(settings.BASE_DIR, 'static')
                    
                    avatar_dir = os.path.join(static_root, 'images', 'avatars')
                    os.makedirs(avatar_dir, exist_ok=True)
                    
                    # Generate unique filename
                    file_ext = os.path.splitext(avatar_file.name)[1]
                    filename = f"{user.username}_{user.id}_{int(time.time())}{file_ext}"
                    filepath = os.path.join(avatar_dir, filename)
                    
                    # Save file
                    with open(filepath, 'wb+') as destination:
                        for chunk in avatar_file.chunks():
                            destination.write(chunk)
                    
                    # Store relative path
                    profile.avatar = f'images/avatars/{filename}'
                
                profile.save()
                
                # Update MongoDB user
                mongo_user = mongodb_manager.get_user_by_username(user.username)
                if mongo_user:
                    mongodb_manager.update_user(str(mongo_user.get('_id')), {
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'phone': profile.phone,
                    })
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('main:profile')
            except Exception as e:
                import traceback
                print(f"Error updating profile: {traceback.format_exc()}")
                messages.error(request, f'Error updating profile: {str(e)}')
        
        elif action == 'change_password':
            try:
                old_password = request.POST.get('old_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                # Validate
                if not old_password:
                    messages.error(request, 'Current password is required')
                    return redirect('main:profile')
                
                if new_password != confirm_password:
                    messages.error(request, 'New passwords do not match')
                    return redirect('main:profile')
                
                if len(new_password) < 8:
                    messages.error(request, 'New password must be at least 8 characters long')
                    return redirect('main:profile')
                
                # Verify old password
                user = request.user
                if not user.check_password(old_password):
                    # Try MongoDB authentication
                    mongo_user = mongodb_manager.get_user_by_username(user.username)
                    if mongo_user:
                        if not mongodb_manager.verify_password(old_password, mongo_user.get('password', '')):
                            messages.error(request, 'Current password is incorrect')
                            return redirect('main:profile')
                    else:
                        messages.error(request, 'Current password is incorrect')
                        return redirect('main:profile')
                
                # Update password in Django
                user.set_password(new_password)
                user.save()
                
                # Update password in MongoDB
                mongo_user = mongodb_manager.get_user_by_username(user.username)
                if mongo_user:
                    import bcrypt
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    mongodb_manager.update_user(str(mongo_user.get('_id')), {
                        'password': hashed_password
                    })
                
                # Re-authenticate user after password change
                from django.contrib.auth import login
                login(request, user)
                
                messages.success(request, 'Password changed successfully!')
                return redirect('main:profile')
            except Exception as e:
                import traceback
                print(f"Error changing password: {traceback.format_exc()}")
                messages.error(request, f'Error changing password: {str(e)}')
        
        elif action == 'save_address':
            # This action is now handled via AJAX - redirect will be handled by JavaScript
            # Keeping this for backward compatibility but it should use MongoDB via AJAX
            try:
                address_id = request.POST.get('address_id')
                mongo_user = mongodb_manager.get_user_by_username(request.user.username)
                if not mongo_user:
                    messages.error(request, 'User not found in MongoDB')
                    return redirect('main:profile')
                
                user_id = str(mongo_user.get('_id'))
                
                # Prepare address data for MongoDB
                address_data = {
                    'user_id': user_id,
                    'address_name': request.POST.get('address_name', ''),
                    'first_name': request.POST.get('first_name', ''),
                    'last_name': request.POST.get('last_name', ''),
                    'address_line1': request.POST.get('address_line1', request.POST.get('address', '')),
                    'address_line2': request.POST.get('address_line2', ''),
                    'city': request.POST.get('city', ''),
                    'state': request.POST.get('province', request.POST.get('state', '')),
                    'postal_code': request.POST.get('postal_code', request.POST.get('zip_code', '')),
                    'country': request.POST.get('country', 'Cambodia'),
                    'phone': request.POST.get('phone', ''),
                    'is_default': request.POST.get('is_default') == 'on',
                }
                
                if address_id:
                    # Update existing address in MongoDB
                    success = mongodb_manager.update_address(address_id, address_data)
                    if success:
                        messages.success(request, 'Address updated successfully!')
                    else:
                        messages.error(request, 'Failed to update address')
                else:
                    # Create new address in MongoDB
                    address_id = mongodb_manager.create_address(address_data)
                    if address_id:
                        messages.success(request, 'Address added successfully!')
                    else:
                        messages.error(request, 'Failed to save address')
                
                return redirect('main:profile')
            except Exception as e:
                import traceback
                print(f"Error saving address: {traceback.format_exc()}")
                messages.error(request, f'Error saving address: {str(e)}')
                return redirect('main:profile')
        
        elif action == 'delete_address':
            try:
                address_id = request.POST.get('address_id')
                mongo_user = mongodb_manager.get_user_by_username(request.user.username)
                if not mongo_user:
                    messages.error(request, 'User not found')
                    return redirect('main:profile')
                
                user_id = str(mongo_user.get('_id'))
                
                # Verify address belongs to user before deleting
                address = mongodb_manager.get_address_by_id(address_id)
                if not address or address.get('user_id') != user_id:
                    messages.error(request, 'Address not found or access denied')
                    return redirect('main:profile')
                
                success = mongodb_manager.delete_address(address_id)
                if success:
                    messages.success(request, 'Address deleted successfully!')
                else:
                    messages.error(request, 'Failed to delete address')
                
                return redirect('main:profile')
            except Exception as e:
                import traceback
                print(f"Error deleting address: {traceback.format_exc()}")
                messages.error(request, f'Error deleting address: {str(e)}')
                return redirect('main:profile')
    
    # GET request - load data
    # Get user profile
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None
    
    # Get user addresses from MongoDB
    addresses = []
    mongo_user = mongodb_manager.get_user_by_username(request.user.username)
    if mongo_user:
        user_id = str(mongo_user.get('_id'))
        addresses = mongodb_manager.get_user_addresses(user_id)
    
    # Get user orders from MongoDB
    mongo_user = mongodb_manager.get_user_by_username(request.user.username)
    orders = []
    if mongo_user:
        user_id = str(mongo_user.get('_id'))
        orders = mongodb_manager.get_user_orders(user_id)
    
    # Get user wishlist from MongoDB
    wishlist_items = []
    if mongo_user:
        user_id = str(mongo_user.get('_id'))
        wishlist_items = mongodb_manager.get_user_wishlist(user_id)
    
    # Cambodia provinces list
    cambodia_provinces = [
        'Phnom Penh', 'Kandal', 'Takeo', 'Kampot', 'Kep', 'Sihanoukville',
        'Kampong Speu', 'Koh Kong', 'Pursat', 'Battambang', 'Pailin',
        'Banteay Meanchey', 'Oddar Meanchey', 'Siem Reap', 'Preah Vihear',
        'Kampong Thom', 'Kampong Cham', 'Tbong Khmum', 'Prey Veng', 'Svay Rieng',
        'Kampong Chhnang', 'Mondulkiri', 'Ratanakiri', 'Stung Treng', 'Kratie'
    ]
    
    context = {
        'page_title': 'Profile',
        'profile': profile,
        'orders': orders,
        'wishlist_items': wishlist_items,
        'addresses': addresses,
        'cambodia_provinces': cambodia_provinces,
    }
    return render(request, 'auth/profile.html', context)

def logout_view(request):
    """User logout view"""
    # Save cart to MongoDB before logout (if user is authenticated)
    if request.user.is_authenticated:
        try:
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if mongo_user:
                user_id = str(mongo_user.get('_id'))
                # Get cart from session or request if available
                # The cart should already be saved via JavaScript before logout
                pass
        except:
            pass
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    # Redirect with a parameter to indicate logout happened
    response = redirect('main:home')
    # Set a cookie to indicate logout happened (for client-side localStorage clearing)
    response.set_cookie('logout_occurred', 'true', max_age=1)
    return response

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
    
    return JsonResponse({'success': False, 'message': 'Cart cleared successfully'})

def checkout(request):
    """Checkout page view"""
    cart_items = []
    saved_addresses = []
    
    if request.user.is_authenticated:
        # Load cart from MongoDB
        mongo_user = mongodb_manager.get_user_by_username(request.user.username)
        if mongo_user:
            user_id = str(mongo_user.get('_id'))
            cart_doc = mongodb_manager.get_user_cart(user_id)
            # Extract cart_data from the cart document
            if cart_doc and isinstance(cart_doc, dict):
                cart_items = cart_doc.get('cart_data', [])
            else:
                cart_items = []
    else:
        # For non-authenticated users, cart is handled client-side via localStorage
        cart_items = []
    
    # Load saved addresses for authenticated users from MongoDB
    if request.user.is_authenticated:
        mongo_user = mongodb_manager.get_user_by_username(request.user.username)
        if mongo_user:
            user_id = str(mongo_user.get('_id'))
            saved_addresses = mongodb_manager.get_user_addresses(user_id)
        else:
            saved_addresses = []
    else:
        saved_addresses = []
    
    context = {
        'page_title': 'Checkout',
        'cart_items': cart_items,
        'saved_addresses': saved_addresses,
    }
    return render(request, 'store/checkout.html', context)


@login_required
@csrf_exempt
def save_cart(request):
    """Save user cart to MongoDB"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_data = data.get('cart', [])
            
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'message': 'User not found'})
            
            user_id = str(mongo_user.get('_id'))
            mongodb_manager.save_user_cart(user_id, cart_data)
            
            return JsonResponse({'success': True, 'message': 'Cart saved successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error saving cart: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def load_cart(request):
    """Load user cart from MongoDB"""
    if request.method == 'GET':
        try:
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'cart': []})
            
            user_id = str(mongo_user.get('_id'))
            cart_doc = mongodb_manager.get_user_cart(user_id)
            
            # Extract cart_data from the cart document
            if cart_doc and isinstance(cart_doc, dict):
                cart_data = cart_doc.get('cart_data', [])
            else:
                cart_data = []
            
            if not cart_data:
                cart_data = []
            
            return JsonResponse({'success': True, 'cart': cart_data})
        except Exception as e:
            import traceback
            print(f"Error loading cart: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'cart': [], 'message': str(e)})
    
    return JsonResponse({'success': False, 'cart': []})


@login_required
@csrf_exempt
def save_address(request):
    """Save user address to MongoDB addresses collection"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get MongoDB user ID
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'message': 'User not found in MongoDB'})
            
            user_id = str(mongo_user.get('_id'))
            
            # Prepare address data for MongoDB
            address_data = {
                'user_id': user_id,
                'address_name': data.get('address_name', ''),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'address_line1': data.get('address', data.get('address_line1', '')),
                'address_line2': data.get('address_line2', ''),
                'city': data.get('city', ''),
                'state': data.get('state', data.get('province', '')),
                'postal_code': data.get('zip_code', data.get('postal_code', '')),
                'country': data.get('country', 'Cambodia'),
                'phone': data.get('phone', ''),
                'is_default': data.get('is_default', False),
            }
            
            # Create address in MongoDB
            address_id = mongodb_manager.create_address(address_data)
            
            if address_id:
                return JsonResponse({'success': True, 'message': 'Address saved successfully', 'address_id': address_id})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to save address'})
        except Exception as e:
            import traceback
            print(f"Error saving address: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'message': f'Error saving address: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def get_addresses(request):
    """Get all addresses for current user from MongoDB"""
    if request.method == 'GET':
        try:
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'addresses': [], 'message': 'User not found in MongoDB'})
            
            user_id = str(mongo_user.get('_id'))
            addresses = mongodb_manager.get_user_addresses(user_id)
            
            # Debug logging
            print(f"DEBUG: Found {len(addresses)} addresses for user {request.user.username}")
            if addresses:
                print(f"DEBUG: First address: {addresses[0]}")
            
            return JsonResponse({'success': True, 'addresses': addresses})
        except Exception as e:
            import traceback
            print(f"Error getting addresses: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'addresses': [], 'message': str(e)})
    
    return JsonResponse({'success': False, 'addresses': [], 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def get_address(request, address_id):
    """Get a specific address by ID from MongoDB"""
    if request.method == 'GET':
        try:
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'address': None, 'message': 'User not found in MongoDB'})
            
            user_id = str(mongo_user.get('_id'))
            address = mongodb_manager.get_address_by_id(address_id)
            
            # Verify address belongs to user
            if not address or address.get('user_id') != user_id:
                return JsonResponse({'success': False, 'address': None, 'message': 'Address not found or access denied'})
            
            return JsonResponse({'success': True, 'address': address})
        except Exception as e:
            import traceback
            print(f"Error getting address: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'address': None, 'message': str(e)})
    
    return JsonResponse({'success': False, 'address': None, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def update_address_mongo(request):
    """Update address in MongoDB"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            address_id = data.get('address_id')
            
            if not address_id:
                return JsonResponse({'success': False, 'message': 'Address ID is required'})
            
            # Get MongoDB user ID
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'message': 'User not found'})
            
            user_id = str(mongo_user.get('_id'))
            
            # Verify address belongs to user
            address = mongodb_manager.get_address_by_id(address_id)
            if not address or address.get('user_id') != user_id:
                return JsonResponse({'success': False, 'message': 'Address not found or access denied'})
            
            # Prepare update data
            update_data = {}
            if 'address_name' in data:
                update_data['address_name'] = data.get('address_name', '')
            if 'first_name' in data:
                update_data['first_name'] = data.get('first_name', '')
            if 'last_name' in data:
                update_data['last_name'] = data.get('last_name', '')
            if 'address' in data or 'address_line1' in data:
                update_data['address_line1'] = data.get('address', data.get('address_line1', ''))
            if 'address_line2' in data:
                update_data['address_line2'] = data.get('address_line2', '')
            if 'city' in data:
                update_data['city'] = data.get('city', '')
            if 'state' in data or 'province' in data:
                update_data['state'] = data.get('state', data.get('province', ''))
            if 'zip_code' in data or 'postal_code' in data:
                update_data['postal_code'] = data.get('zip_code', data.get('postal_code', ''))
            if 'country' in data:
                update_data['country'] = data.get('country', 'Cambodia')
            if 'phone' in data:
                update_data['phone'] = data.get('phone', '')
            if 'is_default' in data:
                update_data['is_default'] = data.get('is_default', False)
            
            success = mongodb_manager.update_address(address_id, update_data)
            
            if success:
                return JsonResponse({'success': True, 'message': 'Address updated successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to update address'})
        except Exception as e:
            import traceback
            print(f"Error updating address: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'message': f'Error updating address: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def delete_address_mongo(request):
    """Delete address from MongoDB"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            address_id = data.get('address_id')
            
            if not address_id:
                return JsonResponse({'success': False, 'message': 'Address ID is required'})
            
            # Get MongoDB user ID
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'message': 'User not found'})
            
            user_id = str(mongo_user.get('_id'))
            
            # Verify address belongs to user
            address = mongodb_manager.get_address_by_id(address_id)
            if not address or address.get('user_id') != user_id:
                return JsonResponse({'success': False, 'message': 'Address not found or access denied'})
            
            success = mongodb_manager.delete_address(address_id)
            
            if success:
                return JsonResponse({'success': True, 'message': 'Address deleted successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to delete address'})
        except Exception as e:
            import traceback
            print(f"Error deleting address: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'message': f'Error deleting address: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def add_wishlist(request):
    """Add product to wishlist"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            
            if not product_id:
                return JsonResponse({'success': False, 'message': 'Product ID is required'})
            
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'message': 'User not found'})
            
            user_id = str(mongo_user.get('_id'))
            mongodb_manager.add_to_wishlist(user_id, product_id)
            
            return JsonResponse({'success': True, 'message': 'Product added to wishlist'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def remove_wishlist(request):
    """Remove product from wishlist"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            
            if not product_id:
                return JsonResponse({'success': False, 'message': 'Product ID is required'})
            
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'message': 'User not found'})
            
            user_id = str(mongo_user.get('_id'))
            mongodb_manager.remove_from_wishlist(user_id, product_id)
            
            return JsonResponse({'success': True, 'message': 'Product removed from wishlist'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def load_wishlist(request):
    """Load user wishlist"""
    if request.method == 'GET':
        try:
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'wishlist': []})
            
            user_id = str(mongo_user.get('_id'))
            wishlist_items = mongodb_manager.get_user_wishlist(user_id)
            
            return JsonResponse({'success': True, 'wishlist': wishlist_items})
        except Exception as e:
            return JsonResponse({'success': False, 'wishlist': [], 'message': str(e)})
    
    return JsonResponse({'success': False, 'wishlist': []})


@login_required
@csrf_exempt
def create_order(request):
    """Create order when user places order from checkout"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get MongoDB user ID
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'message': 'User not found in MongoDB'})
            
            user_id = str(mongo_user.get('_id'))
            
            # Validate cart items
            cart_items = data.get('cart_items', [])
            if not cart_items or len(cart_items) == 0:
                return JsonResponse({'success': False, 'message': 'Cart is empty'})
            
            # Calculate totals
            subtotal = float(data.get('subtotal', 0))
            shipping_cost = float(data.get('shipping_cost', 0))
            tax_amount = float(data.get('tax_amount', 0))
            total_amount = float(data.get('total_amount', 0))
            
            # Prepare shipping address
            shipping_address = {
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'email': data.get('email', ''),
                'phone': data.get('phone', ''),
                'address': data.get('address', ''),
                'city': data.get('city', ''),
                'province': data.get('province', ''),
                'postal_code': data.get('zip_code', ''),
                'country': data.get('country', 'Cambodia'),
            }
            
            # Determine payment method
            payment_method = data.get('payment', 'pay_later')
            if payment_method == 'pay_later':
                payment_status = 'pending'
            else:
                payment_status = 'pending'  # Will be updated after payment
            
            # Create order in MongoDB
            order_data = {
                'user_id': user_id,
                'items': cart_items,
                'subtotal': subtotal,
                'shipping_cost': shipping_cost or 0,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'status': 'pending',
                'payment_status': payment_status,
                'shipping_address': shipping_address,
                'payment_method': payment_method,
                'shipping_method': 'standard',
                'notes': data.get('order_notes', ''),
            }
            
            order_id = mongodb_manager.create_order(order_data)
            
            if not order_id:
                return JsonResponse({'success': False, 'message': 'Failed to create order'})
            
            # Get order number from created order
            order = mongodb_manager.get_order_by_id(order_id)
            order_number = order.get('order_number', '') if order else ''
            
            # Create payment record for all orders (including pay_later)
            # Convert order_id and user_id to ObjectId for MongoDB
            from bson import ObjectId
            try:
                payment_data = {
                    'order_id': ObjectId(order_id) if isinstance(order_id, str) else order_id,  # Convert to ObjectId
                    'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id,    # Convert to ObjectId
                    'amount': total_amount,
                    'payment_method': payment_method,
                    'status': 'pending',
                    'currency': 'USD',
                    'payment_details': {}
                }
                
                payment_id = mongodb_manager.create_payment(payment_data)
                
                if not payment_id:
                    print(f"Warning: Order {order_id} created but payment record failed")
                    import traceback
                    print(traceback.format_exc())
            except Exception as e:
                print(f"Error creating payment record: {e}")
                import traceback
                print(traceback.format_exc())
                payment_id = None
            
            # IMPORTANT: Do NOT remove cart items here
            # Cart items will only be removed after successful payment completion
            # This allows users to keep items in cart if they choose "pay_later" or if payment fails
            
            # Send email notification (order placed)
            try:
                recipient = request.user.email
                if recipient:
                    order_url = request.build_absolute_uri(reverse('main:order_detail', args=[order_id]))
                    subject = f"Order {order_number or order_id} placed"
                    context_email = {
                        'user_name': request.user.get_full_name() or request.user.username,
                        'order_number': order_number or order_id,
                        'total_amount': f"${total_amount:.2f}",
                        'payment_method': payment_method,
                        'order_url': order_url,
                        'cta_label': 'View your order',
                        'headline': 'Thanks for your order!',
                        'subtext': 'We are preparing your items.'
                    }
                    send_html_email(subject, 'emails/order_placed.html', context_email, recipient)
            except Exception as e:
                logger.exception(f"Email send failed (order placed). To={getattr(request.user, 'email', None)} Host={getattr(settings, 'EMAIL_HOST', None)} User={getattr(settings, 'EMAIL_HOST_USER', None)} Port={getattr(settings, 'EMAIL_PORT', None)} TLS={getattr(settings, 'EMAIL_USE_TLS', None)}: {e}")
            
            # Send Telegram notification to owner (new order placed)
            try:
                order_notification_data = {
                    'order_number': order_number or order_id,
                    'total_amount': total_amount,
                    'payment_method': payment_method,
                    'customer_name': request.user.get_full_name() or request.user.username,
                    'customer_email': request.user.email or '',
                    'items': cart_items,
                    'shipping_address': shipping_address,
                }
                send_order_notification(order_notification_data)
            except Exception as e:
                logger.exception(f"Telegram notification failed (order placed): {e}")

            return JsonResponse({
                'success': True,
                'message': 'Order placed successfully!',
                'order_id': str(order_id),
                'order_number': order_number,
                'payment_id': str(payment_id) if payment_id else None,
            })
            
        except Exception as e:
            import traceback
            print(f"Error creating order: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'message': f'Error creating order: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def payment(request):
    """Payment page - handles PayPal redirect or Bakong QR code display"""
    order_id = request.GET.get('order_id')
    order_number = request.GET.get('order_number')
    payment_method = request.GET.get('payment_method', 'paypal')
    
    if not order_id:
        messages.error(request, 'Order ID is required')
        return redirect('main:checkout')
    
    # Get order from MongoDB
    order = mongodb_manager.get_order_by_id(order_id)
    if not order:
        messages.error(request, 'Order not found')
        return redirect('main:checkout')
    
    # Check if order belongs to user (if authenticated)
    if request.user.is_authenticated:
        mongo_user = mongodb_manager.get_user_by_username(request.user.username)
        if mongo_user:
            user_id = str(mongo_user.get('_id'))
            if order.get('user_id') != user_id:
                messages.error(request, 'You do not have permission to view this order')
                return redirect('main:home')
    
    # Get payment_id from payment record
    payment_id = None
    try:
        from bson import ObjectId
        from pymongo import DESCENDING
        payment_doc = mongodb_manager.payments_collection.find_one({
            'order_id': ObjectId(order_id)
        }, sort=[('created_at', DESCENDING)])
        
        if payment_doc:
            payment_id = str(payment_doc.get('_id'))
    except:
        pass
    
    context = {
        'order': order,
        'order_id': order_id,
        'order_number': order_number or order.get('order_number', ''),
        'payment_method': payment_method,
        'total_amount': order.get('total_amount', 0),
        'payment_id': payment_id,
        'paypal_client_id': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
    }
    
    return render(request, 'store/payment.html', context)

# --- PayPal Integration ---
import requests

def _paypal_base_url():
    env = getattr(settings, 'PAYPAL_ENV', 'sandbox')
    return 'https://api-m.sandbox.paypal.com' if env != 'live' else 'https://api-m.paypal.com'

def _paypal_access_token():
    client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
    client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        raise ValueError('PayPal client credentials are not configured')
    resp = requests.post(
        f"{_paypal_base_url()}/v1/oauth2/token",
        headers={'Accept': 'application/json', 'Accept-Language': 'en_US'},
        data={'grant_type': 'client_credentials'},
        auth=(client_id, client_secret),
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get('access_token')


@login_required
@csrf_exempt
def paypal_create_order(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)
    try:
        body = json.loads(request.body or '{}')
    except Exception:
        body = {}
    order_id = request.GET.get('order_id') or body.get('order_id')
    if not order_id:
        return JsonResponse({'success': False, 'message': 'order_id is required'}, status=400)
    order = mongodb_manager.get_order_by_id(order_id)
    if not order:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)

    # Sanitize amount for PayPal: 2 decimals, minimum 0.01
    try:
        amount = float(order.get('total_amount', 0) or 0)
    except Exception:
        amount = 0.0
    amount = round(amount + 1e-8, 2)
    if amount < 0.01:
        amount = 0.01
    currency = 'USD'
    try:
        access_token = _paypal_access_token()
        # Build return/cancel URLs for redirect flow
        return_url = request.build_absolute_uri(reverse('main:paypal_return')) + f"?order_id={order_id}"
        cancel_url = request.build_absolute_uri(reverse('main:paypal_cancel')) + f"?order_id={order_id}"

        payload = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'reference_id': order.get('order_number', order_id),
                'amount': {
                    'currency_code': currency,
                    'value': f"{amount:.2f}"
                }
            }],
            'application_context': {
                'return_url': return_url,
                'cancel_url': cancel_url
            }
        }
        resp = requests.post(
            f"{_paypal_base_url()}/v2/checkout/orders",
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            },
            json=payload,
            timeout=30,
        )
        data = resp.json()
        if resp.status_code not in (200, 201):
            logger.error(f"PayPal create error: status={resp.status_code} data={data}")
            return JsonResponse({'success': False, 'message': data}, status=400)

        paypal_order_id = data.get('id')
        # Mark order intent as PayPal pending
        try:
            from bson import ObjectId
            mongodb_manager.orders_collection.update_one(
                {'_id': ObjectId(order_id)},
                {'$set': {'payment_method': 'PayPal', 'payment_status': 'pending'}}
            )
        except Exception:
            pass

        return JsonResponse({'success': True, 'paypal_order_id': paypal_order_id, 'data': data})
    except Exception as e:
        logger.exception(f"PayPal create order failed: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@csrf_exempt
def paypal_capture_order(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)
    try:
        body = json.loads(request.body or '{}')
    except Exception:
        body = {}
    paypal_order_id = request.GET.get('paypal_order_id') or body.get('paypal_order_id')
    order_id = request.GET.get('order_id') or body.get('order_id')
    if not paypal_order_id or not order_id:
        return JsonResponse({'success': False, 'message': 'paypal_order_id and order_id are required'}, status=400)

    order = mongodb_manager.get_order_by_id(order_id)
    if not order:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)

    try:
        access_token = _paypal_access_token()
        resp = requests.post(
            f"{_paypal_base_url()}/v2/checkout/orders/{paypal_order_id}/capture",
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            },
            timeout=30,
        )
        data = resp.json()
        if resp.status_code not in (200, 201):
            logger.error(f"PayPal capture error: status={resp.status_code} data={data}")
            return JsonResponse({'success': False, 'message': data}, status=400)

        status = data.get('status')
        if status == 'COMPLETED':
            # Update payment + order status
            try:
                from bson import ObjectId
                mongodb_manager.orders_collection.update_one(
                    {'_id': ObjectId(order_id)},
                    {'$set': {'status': 'completed', 'payment_status': 'completed', 'payment_method': 'PayPal'}}
                )
            except Exception:
                pass

            # Send email: payment received
            try:
                recipient = request.user.email
                if recipient:
                    order_url = request.build_absolute_uri(reverse('main:order_detail', args=[order_id]))
                    subject = f"Payment received for Order {order.get('order_number', order_id)}"
                    context_email = {
                        'user_name': request.user.get_full_name() or request.user.username,
                        'order_number': order.get('order_number', order_id),
                        'total_amount': f"${order.get('total_amount', 0):.2f}",
                        'payment_method': 'PayPal',
                        'order_url': order_url,
                        'cta_label': 'View your order',
                        'headline': 'Payment received ✔',
                        'subtext': 'Your order is now being processed.'
                    }
                    send_html_email(subject, 'emails/payment_received.html', context_email, recipient)
            except Exception as e:
                logger.exception(f"Email send failed (PayPal payment). {e}")
            
            # Send Telegram notification to owner (payment received)
            try:
                payment_notification_data = {
                    'order_number': order.get('order_number', order_id),
                    'total_amount': order.get('total_amount', 0),
                    'payment_method': 'PayPal',
                    'customer_name': request.user.get_full_name() or request.user.username,
                    'customer_email': request.user.email or '',
                    'items': order.get('items', []),
                }
                send_payment_notification(payment_notification_data)
            except Exception as e:
                logger.exception(f"Telegram notification failed (PayPal payment): {e}")

            return JsonResponse({'success': True, 'order_id': order_id, 'order_number': order.get('order_number', '')})

        return JsonResponse({'success': False, 'message': 'Capture not completed', 'data': data}, status=400)
    except Exception as e:
        logger.exception(f"PayPal capture order failed: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def paypal_return(request):
    """Handle PayPal redirect return and capture payment."""
    paypal_order_id = request.GET.get('token')  # PayPal sends token=orderID
    order_id = request.GET.get('order_id')
    if not paypal_order_id or not order_id:
        messages.error(request, 'Missing PayPal token or order id')
        return redirect('main:payment')
    # Reuse capture logic
    try:
        access_token = _paypal_access_token()
        resp = requests.post(
            f"{_paypal_base_url()}/v2/checkout/orders/{paypal_order_id}/capture",
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            },
            timeout=30,
        )
        data = resp.json()
        if resp.status_code in (200, 201) and data.get('status') == 'COMPLETED':
            # Update order
            try:
                from bson import ObjectId
                mongodb_manager.orders_collection.update_one(
                    {'_id': ObjectId(order_id)},
                    {'$set': {'status': 'completed', 'payment_status': 'completed', 'payment_method': 'PayPal'}}
                )
            except Exception:
                pass
            # Email
            try:
                recipient = request.user.email
                order = mongodb_manager.get_order_by_id(order_id) or {}
                if recipient:
                    order_url = request.build_absolute_uri(reverse('main:order_detail', args=[order_id]))
                    subject = f"Payment received for Order {order.get('order_number', order_id)}"
                    context_email = {
                        'user_name': request.user.get_full_name() or request.user.username,
                        'order_number': order.get('order_number', order_id),
                        'total_amount': f"${order.get('total_amount', 0):.2f}",
                        'payment_method': 'PayPal',
                        'order_url': order_url,
                        'cta_label': 'View your order',
                        'headline': 'Payment received ✔',
                        'subtext': 'Your order is now being processed.'
                    }
                    send_html_email(subject, 'emails/payment_received.html', context_email, recipient)
            except Exception as e:
                logger.exception(f"Email send failed (PayPal return). {e}")
            
            # Send Telegram notification to owner (payment received via redirect)
            try:
                order = mongodb_manager.get_order_by_id(order_id) or {}
                payment_notification_data = {
                    'order_number': order.get('order_number', order_id),
                    'total_amount': order.get('total_amount', 0),
                    'payment_method': 'PayPal',
                    'customer_name': request.user.get_full_name() or request.user.username,
                    'customer_email': request.user.email or '',
                    'items': order.get('items', []),
                }
                send_payment_notification(payment_notification_data)
            except Exception as e:
                logger.exception(f"Telegram notification failed (PayPal return): {e}")
            
            # Redirect to thanks
            order = mongodb_manager.get_order_by_id(order_id) or {}
            return redirect(f"{reverse('main:order_thanks')}?order_id={order_id}&order_number={order.get('order_number','')}")
        else:
            logger.error(f"PayPal return capture failed: status={resp.status_code} data={data}")
            messages.error(request, 'Payment capture failed. Please try again or choose another method.')
            return redirect(f"{reverse('main:payment')}?order_id={order_id}&order_number={mongodb_manager.get_order_by_id(order_id).get('order_number','')}&payment_method=paypal")
    except Exception as e:
        logger.exception(f"PayPal return error: {e}")
        messages.error(request, 'Payment error. Please try again later.')
        return redirect('main:checkout')


@login_required
def paypal_cancel(request):
    """Handle PayPal redirect cancel."""
    order_id = request.GET.get('order_id')
    messages.info(request, 'PayPal payment was cancelled.')
    if order_id:
        order = mongodb_manager.get_order_by_id(order_id) or {}
        return redirect(f"{reverse('main:payment')}?order_id={order_id}&order_number={order.get('order_number','')}&payment_method=paypal")
    return redirect('main:checkout')


@login_required
@csrf_exempt
def generate_bakong_qr(request):
    """Generate Bakong KHQR QR code for order payment"""
    if request.method == 'GET':
        try:
            order_id = request.GET.get('order_id')
            if not order_id:
                return JsonResponse({'success': False, 'message': 'Order ID is required'})
            
            # Get order from MongoDB
            order = mongodb_manager.get_order_by_id(order_id)
            if not order:
                return JsonResponse({'success': False, 'message': 'Order not found'})
            
            # Get Bakong configuration from environment variables
            from decouple import config
            from django.conf import settings
            import os
            
            # Get project root directory
            project_root = settings.BASE_DIR
            
            # Try to read from .env file
            bakong_token = config('BAKONG_TOKEN', default='', cast=str).strip()
            bakong_account = config('BAKONG_ACCOUNT', default='', cast=str).strip()
            merchant_name = config('BAKONG_MERCHANT_NAME', default='ECommerce Store', cast=str).strip()
            merchant_city = config('BAKONG_MERCHANT_CITY', default='Phnom Penh', cast=str).strip()
            phone_number = config('BAKONG_PHONE', default='85512345678', cast=str).strip()
            store_label = config('BAKONG_STORE_LABEL', default='Store', cast=str).strip()
            terminal_label = config('BAKONG_TERMINAL_LABEL', default='Terminal-01', cast=str).strip()
            
            # Debug: Print values (remove in production)
            print(f"DEBUG: BAKONG_TOKEN found: {bool(bakong_token)}, length: {len(bakong_token)}")
            print(f"DEBUG: BAKONG_ACCOUNT found: {bool(bakong_account)}, value: {bakong_account[:20]}...")
            
            if not bakong_token or not bakong_account:
                return JsonResponse({
                    'success': False,
                    'message': f'Bakong configuration is missing. BAKONG_TOKEN: {"Set" if bakong_token else "Not Set"}, BAKONG_ACCOUNT: {"Set" if bakong_account else "Not Set"}. Please check your .env file in the project root directory.'
                })
            
            # Use USD amount directly
            amount_usd = order.get('total_amount', 0)
            
            # Import Bakong KHQR
            try:
                from bakong_khqr import KHQR
            except ImportError:
                return JsonResponse({
                    'success': False,
                    'message': 'Bakong KHQR package is not installed. Please run: pip install bakong-khqr'
                })
            
            # Create KHQR instance
            khqr = KHQR(bakong_token)
            
            # Generate QR code string
            qr_string = khqr.create_qr(
                bank_account=bakong_account,
                merchant_name=merchant_name,
                merchant_city=merchant_city,
                amount=amount_usd,
                currency='USD',
                store_label=store_label,
                phone_number=phone_number,
                bill_number=order.get('order_number', ''),
                terminal_label=terminal_label,
                static=False
            )
            
            # Generate MD5 hash for payment tracking
            md5_hash = khqr.generate_md5(qr_string)
            
            # Generate QR code image
            try:
                qr_image_path = khqr.qr_image(qr_string, format='base64_uri')
                qr_image_base64 = qr_image_path.split(',')[1] if ',' in qr_image_path else None
                qr_image_url = qr_image_path
            except Exception as e:
                print(f"Error generating QR image: {e}")
                qr_image_base64 = None
                qr_image_url = None
            
            # Store MD5 hash in payment record for tracking
            payment_id = request.GET.get('payment_id')
            if payment_id:
                from bson import ObjectId
                from pymongo import DESCENDING
                payment_doc = mongodb_manager.payments_collection.find_one({
                    'order_id': ObjectId(order_id)
                }, sort=[('created_at', DESCENDING)])
                
                if payment_doc:
                    payment_id = str(payment_doc.get('_id'))
                    mongodb_manager.update_payment_status(payment_id, 'pending', {
                        'md5_hash': md5_hash,
                        'qr_string': qr_string,
                    })
            
            return JsonResponse({
                'success': True,
                'qr_code_data': qr_string,
                'md5_hash': md5_hash,
                'qr_image_url': qr_image_url,
                'qr_image_base64': qr_image_base64,
                'amount_usd': amount_usd,
            })
            
        except Exception as e:
            import traceback
            print(f"Error generating Bakong QR: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': f'Error generating QR code: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def check_payment_status(request):
    """Check if Bakong payment has been completed"""
    if request.method == 'GET':
        try:
            order_id = request.GET.get('order_id')
            if not order_id:
                return JsonResponse({'success': False, 'paid': False, 'message': 'Order ID is required'})
            
            # Get order from MongoDB
            order = mongodb_manager.get_order_by_id(order_id)
            if not order:
                return JsonResponse({'success': False, 'paid': False, 'message': 'Order not found'})
            
            # Get payment record
            from bson import ObjectId
            from pymongo import DESCENDING
            
            payment_doc = mongodb_manager.payments_collection.find_one({
                'order_id': ObjectId(order_id)
            }, sort=[('created_at', DESCENDING)])
            
            if not payment_doc:
                return JsonResponse({'paid': False, 'message': 'Payment record not found'})
            
            md5_hash = payment_doc.get('payment_details', {}).get('md5_hash')
            if not md5_hash:
                return JsonResponse({'paid': False, 'message': 'MD5 hash not found'})
            
            # Check payment status using Bakong API
            try:
                from bakong_khqr import KHQR
                from decouple import config
                
                bakong_token = config('BAKONG_TOKEN', default='', cast=str).strip()
                if not bakong_token:
                    return JsonResponse({'paid': False, 'message': 'Bakong token not configured. Please check your .env file.'})
                
                khqr = KHQR(bakong_token)
                payment_status = khqr.check_payment(md5_hash)
                
                is_paid = payment_status == 'PAID' or payment_status == 'paid'
                
                # Update payment and order status if paid
                if is_paid:
                    payment_id = str(payment_doc.get('_id'))
                    mongodb_manager.update_payment_status(payment_id, 'completed')
                    # Update both order status and payment_status
                    mongodb_manager.update_order_status(order_id, 'completed', payment_status='completed')
                    # Ensure payment_method is set to the actual method (Bakong here)
                    try:
                        from bson import ObjectId
                        mongodb_manager.orders_collection.update_one(
                            {'_id': ObjectId(order_id)},
                            {'$set': {'payment_method': 'Bakong'}}
                        )
                        order['payment_method'] = 'Bakong'
                    except Exception:
                        pass
                    # Email: payment completed
                    try:
                        recipient = request.user.email
                        if recipient:
                            order_url = request.build_absolute_uri(reverse('main:order_detail', args=[order_id]))
                            subject = f"Payment received for Order {order.get('order_number', order_id)}"
                            context_email = {
                                'user_name': request.user.get_full_name() or request.user.username,
                                'order_number': order.get('order_number', order_id),
                                'total_amount': f"${order.get('total_amount', 0):.2f}",
                                'payment_method': order.get('payment_method', 'Bakong'),
                                'order_url': order_url,
                                'cta_label': 'View your order',
                                'headline': 'Payment received ✔',
                                'subtext': 'Your order is now being processed.'
                            }
                            send_html_email(subject, 'emails/payment_received.html', context_email, recipient)
                    except Exception as e:
                        logger.exception(f"Email send failed (payment completed). To={getattr(request.user, 'email', None)} Host={getattr(settings, 'EMAIL_HOST', None)} User={getattr(settings, 'EMAIL_HOST_USER', None)} Port={getattr(settings, 'EMAIL_PORT', None)} TLS={getattr(settings, 'EMAIL_USE_TLS', None)}: {e}")
                    
                    # Send Telegram notification to owner (Bakong payment completed)
                    try:
                        payment_notification_data = {
                            'order_number': order.get('order_number', order_id),
                            'total_amount': order.get('total_amount', 0),
                            'payment_method': order.get('payment_method', 'Bakong'),
                            'customer_name': request.user.get_full_name() or request.user.username,
                            'customer_email': request.user.email or '',
                            'items': order.get('items', []),
                        }
                        send_payment_notification(payment_notification_data)
                    except Exception as e:
                        logger.exception(f"Telegram notification failed (Bakong payment): {e}")
                    
                    # Clear only selected items from user's cart after successful payment
                    # The frontend will handle removing only checkoutItems from localStorage
                    # We'll update the cart on server with remaining items when frontend calls save_cart
                    
                    return JsonResponse({
                        'paid': True,
                        'message': 'Payment completed successfully!'
                    })
                else:
                    return JsonResponse({
                        'paid': False,
                        'message': 'Payment is still pending'
                    })
                    
            except ImportError:
                return JsonResponse({
                    'paid': False,
                    'message': 'Bakong KHQR package is not installed'
                })
            except Exception as e:
                print(f"Error checking payment status: {e}")
                return JsonResponse({
                    'paid': False,
                    'message': f'Error checking payment: {str(e)}'
                })
            
        except Exception as e:
            import traceback
            print(f"Error checking payment status: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'paid': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'paid': False, 'message': 'Invalid request method'})


def order_thanks(request):
    """Thank you page after successful order"""
    order_id = request.GET.get('order_id')
    order_number = request.GET.get('order_number', '')
    pay_later = request.GET.get('pay_later') == 'true'
    
    # Get order details if available
    order = None
    if order_id:
        order = mongodb_manager.get_order_by_id(order_id)
        if order:
            order_number = order.get('order_number', order_number)
    
    context = {
        'page_title': 'Thank You',
        'order_id': order_id,
        'order_number': order_number,
        'order': order,
        'pay_later': pay_later,
    }
    
    return render(request, 'store/order_thanks.html', context)


@login_required
def order_detail(request, order_id):
    """Order detail view"""
    # Get order from MongoDB
    order = mongodb_manager.get_order_by_id(order_id)
    
    if not order:
        messages.error(request, 'Order not found')
        return redirect('main:profile')
    
    # Check if order belongs to user
    if request.user.is_authenticated:
        mongo_user = mongodb_manager.get_user_by_username(request.user.username)
        if mongo_user:
            user_id = str(mongo_user.get('_id'))
            if order.get('user_id') != user_id:
                messages.error(request, 'You do not have permission to view this order')
                return redirect('main:home')
    
    context = {
        'page_title': f'Order #{order.get("order_number", order_id)}',
        'order': order,
    }
    
    return render(request, 'store/order_detail.html', context)


@login_required
@csrf_exempt
def cancel_order(request):
    """Cancel an order"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            
            if not order_id:
                return JsonResponse({'success': False, 'message': 'Order ID is required'})
            
            # Get order from MongoDB
            order = mongodb_manager.get_order_by_id(order_id)
            if not order:
                return JsonResponse({'success': False, 'message': 'Order not found'})
            
            # Check if order belongs to user
            mongo_user = mongodb_manager.get_user_by_username(request.user.username)
            if not mongo_user:
                return JsonResponse({'success': False, 'message': 'User not found'})
            
            user_id = str(mongo_user.get('_id'))
            if order.get('user_id') != user_id:
                return JsonResponse({'success': False, 'message': 'You do not have permission to cancel this order'})
            
            # Check if order can be cancelled (only pending or processing orders)
            if order.get('status') in ['completed', 'cancelled', 'shipped']:
                return JsonResponse({'success': False, 'message': f'Cannot cancel order with status: {order.get("status")}'})
            
            # Cancel the order and optionally cancel payment status
            cancel_payment = data.get('cancel_payment', False)
            if cancel_payment:
                # Attempt to mark latest payment as cancelled
                try:
                    from bson import ObjectId
                    from pymongo import DESCENDING
                    payment_doc = mongodb_manager.payments_collection.find_one({
                        'order_id': ObjectId(order_id)
                    }, sort=[('created_at', DESCENDING)])
                    if payment_doc:
                        mongodb_manager.update_payment_status(str(payment_doc.get('_id')), 'cancelled')
                except Exception:
                    pass
            success = mongodb_manager.update_order_status(order_id, 'cancelled', payment_status='cancelled' if cancel_payment else order.get('payment_status', 'pending'))
            
            if success:
                # Send cancellation email
                try:
                    recipient = request.user.email
                    if recipient:
                        order_url = request.build_absolute_uri(reverse('main:order_detail', args=[order_id]))
                        subject = f"Order {order.get('order_number', order_id)} cancelled"
                        context_email = {
                            'user_name': request.user.get_full_name() or request.user.username,
                            'order_number': order.get('order_number', order_id),
                            'total_amount': f"${order.get('total_amount', 0):.2f}",
                            'payment_method': order.get('payment_method', ''),
                            'order_url': order_url,
                            'cta_label': 'View order details',
                            'headline': 'Your order was cancelled',
                            'subtext': 'If this was a mistake, you can place a new order.'
                        }
                        send_html_email(subject, 'emails/order_cancelled.html', context_email, recipient)
                except Exception as e:
                    logger.exception(f"Email send failed (order cancelled). To={getattr(request.user, 'email', None)} Host={getattr(settings, 'EMAIL_HOST', None)} User={getattr(settings, 'EMAIL_HOST_USER', None)} Port={getattr(settings, 'EMAIL_PORT', None)} TLS={getattr(settings, 'EMAIL_USE_TLS', None)}: {e}")
                return JsonResponse({'success': True, 'message': 'Order cancelled successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to cancel order'})
                
        except Exception as e:
            import traceback
            print(f"Error cancelling order: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'message': f'Error cancelling order: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
