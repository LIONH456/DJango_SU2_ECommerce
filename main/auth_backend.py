from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .mongodb_utils import mongodb_manager
from django.contrib.auth.hashers import make_password, check_password

User = get_user_model()

class MongoDBBackend(BaseBackend):
    """
    Custom authentication backend for MongoDB
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        # Try to get user from MongoDB
        mongo_user = mongodb_manager.get_user_by_username(username)
        if not mongo_user:
            return None
        
        # Check if user is active
        if not mongo_user.get('is_active', True):
            return None
        
        # Verify password
        if mongodb_manager.verify_password(username, password):
            # Update last login
            mongodb_manager.update_last_login(username)
            
            # Create or get Django User object
            django_user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': mongo_user.get('email', ''),
                    'first_name': mongo_user.get('first_name', ''),
                    'last_name': mongo_user.get('last_name', ''),
                    'is_active': mongo_user.get('is_active', True),
                    'is_staff': mongo_user.get('is_staff', False),
                    'is_superuser': mongo_user.get('is_superuser', False),
                    'date_joined': mongo_user.get('date_joined'),
                    'last_login': mongo_user.get('last_login'),
                }
            )
            
            # Update Django user if not created
            if not created:
                django_user.email = mongo_user.get('email', '')
                django_user.first_name = mongo_user.get('first_name', '')
                django_user.last_name = mongo_user.get('last_name', '')
                django_user.is_active = mongo_user.get('is_active', True)
                django_user.is_staff = mongo_user.get('is_staff', False)
                django_user.is_superuser = mongo_user.get('is_superuser', False)
                django_user.last_login = mongo_user.get('last_login')
                django_user.save()
            
            return django_user
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

