from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserAddress, UserProfile, UserSession, UserActivity

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'display_name', 'avatar', 'phone',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'phone'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserAddressSerializer(serializers.ModelSerializer):
    """Serializer for UserAddress model"""
    
    class Meta:
        model = UserAddress
        fields = [
            'id', 'user', 'address_type', 'first_name', 'last_name',
            'company', 'address_line1', 'address_line2', 'city',
            'state', 'country', 'postal_code', 'phone',
            'is_default', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'bio', 'website', 'social_links',
            'language', 'timezone', 'currency',
            'wishlist_count', 'order_count', 'total_spent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for UserSession model"""
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user', 'session_id', 'ip_address',
            'user_agent', 'is_active', 'last_activity',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for UserActivity model"""
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'description',
            'ip_address', 'user_agent', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

