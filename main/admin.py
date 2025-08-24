from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserAddress, UserProfile, UserSession, UserActivity

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    """Admin for UserAddress model"""
    
    list_display = ('user', 'address_type', 'first_name', 'last_name', 'city', 'country', 'is_default', 'is_active')
    list_filter = ('address_type', 'is_default', 'is_active', 'country', 'created_at')
    search_fields = ('user__username', 'user__email', 'first_name', 'last_name', 'city', 'country')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'address_type')
        }),
        ('Address Details', {
            'fields': (
                'first_name', 'last_name', 'company', 'address_line1', 
                'address_line2', 'city', 'state', 'country', 'postal_code', 'phone'
            )
        }),
        ('Status', {
            'fields': ('is_default', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model"""
    
    list_display = ('user', 'language', 'currency', 'wishlist_count', 'order_count', 'total_spent')
    list_filter = ('language', 'currency', 'created_at')
    search_fields = ('user__username', 'user__email', 'bio')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': ('bio', 'website', 'social_links')
        }),
        ('Preferences', {
            'fields': ('language', 'timezone', 'currency')
        }),
        ('E-commerce Stats', {
            'fields': ('wishlist_count', 'order_count', 'total_spent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin for UserSession model"""
    
    list_display = ('user', 'session_id', 'ip_address', 'is_active', 'last_activity', 'created_at')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'session_id', 'ip_address')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'session_id', 'ip_address', 'user_agent')
        }),
        ('Status', {
            'fields': ('is_active', 'last_activity', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'last_activity')

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin for UserActivity model"""
    
    list_display = ('user', 'activity_type', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'description', 'ip_address')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('user', 'activity_type', 'description')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def has_add_permission(self, request):
        """Disable manual addition of activities"""
        return False
