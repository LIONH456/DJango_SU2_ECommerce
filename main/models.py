from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """Custom User model for MongoDB integration"""
    
    # Basic user information
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Contact information
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self):
        return self.full_name or self.username

class UserAddress(models.Model):
    """User addresses for shipping/billing"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=[
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
        ('both', 'Both')
    ], default='shipping')
    
    # Address label/name for easy identification
    address_name = models.CharField(max_length=100, blank=True, null=True, help_text="Name/label for this address (e.g., 'Home', 'Work', 'Office')")
    
    # Address details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True, null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    
    # Address status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_addresses'
        verbose_name = 'User Address'
        verbose_name_plural = 'User Addresses'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.address_type}"

class UserProfile(models.Model):
    """Extended user profile information"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Additional profile fields
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    social_links = models.JSONField(default=dict, blank=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)  # Store path to avatar image
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Preferences
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    
    # E-commerce specific
    wishlist_count = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.username}"

class UserSession(models.Model):
    """User session tracking"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Session details
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
    
    def __str__(self):
        return f"Session {self.session_id} for {self.user.username}"

class UserActivity(models.Model):
    """User activity logging"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=[
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('register', 'Registration'),
        ('password_change', 'Password Change'),
        ('profile_update', 'Profile Update'),
        ('order_placed', 'Order Placed'),
        ('product_view', 'Product View'),
        ('wishlist_add', 'Wishlist Add'),
        ('review_posted', 'Review Posted'),
    ])
    
    # Activity details
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.created_at}"

class UserCart(models.Model):
    """User shopping cart stored in database"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    cart_data = models.JSONField(default=list)  # Store cart items as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_carts'
        verbose_name = 'User Cart'
        verbose_name_plural = 'User Carts'
        # One cart per user (get_or_create pattern)
    
    def __str__(self):
        return f"Cart for {self.user.username}"
