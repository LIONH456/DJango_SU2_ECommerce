#!/usr/bin/env python3
"""
Test production settings locally
"""

import os
import django
from django.conf import settings

# Set environment variables for production testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ECommerce.settings')
os.environ['DEBUG'] = 'False'
os.environ['MONGODB_ATLAS_URI'] = 'mongodb+srv://lionh456:LVixKN2699pd2wpO@ecommercesu2.xcvh6ig.mongodb.net/?retryWrites=true&w=majority&appName=EcommerceSU2'

# Setup Django
django.setup()

def test_production_settings():
    """Test production settings"""
    print("🧪 Testing Production Settings")
    print("=" * 40)
    
    # Test basic settings
    print(f"✅ DEBUG: {settings.DEBUG}")
    print(f"✅ SECRET_KEY: {'Set' if settings.SECRET_KEY else 'Not Set'}")
    print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
    # Test MongoDB configuration
    print(f"\n🗄️  MongoDB Configuration:")
    print(f"  - Database: {settings.MONGODB_CONFIG['database']}")
    print(f"  - Collection: {settings.MONGODB_CONFIG['collection']}")
    print(f"  - Atlas URI: {'Set' if settings.MONGODB_CONFIG.get('atlas_uri') else 'Not Set'}")
    
    # Test static files
    print(f"\n📁 Static Files:")
    print(f"  - STATIC_URL: {settings.STATIC_URL}")
    print(f"  - STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"  - STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    
    # Test database configuration
    print(f"\n💾 Database Configuration:")
    print(f"  - Engine: {settings.DATABASES['default']['ENGINE']}")
    if 'NAME' in settings.DATABASES['default']:
        print(f"  - Name: {settings.DATABASES['default']['NAME']}")
    
    # Test authentication
    print(f"\n🔐 Authentication:")
    print(f"  - AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
    print(f"  - AUTHENTICATION_BACKENDS: {len(settings.AUTHENTICATION_BACKENDS)} backends")
    
    # Test MongoDB connection
    try:
        from main.mongodb_utils import mongodb_manager
        print(f"\n🔌 MongoDB Connection Test:")
        
        # Test connection
        mongodb_manager.client.admin.command('ping')
        print("  ✅ MongoDB connection successful")
        
        # Test database access
        db = mongodb_manager.client[settings.MONGODB_CONFIG['database']]
        collections = db.list_collection_names()
        print(f"  ✅ Database accessible, {len(collections)} collections found")
        
        # Test user collection
        if 'users' in collections:
            user_count = db.users.count_documents({})
            print(f"  ✅ Users collection accessible, {user_count} users found")
        else:
            print("  ⚠️  Users collection not found")
            
    except Exception as e:
        print(f"  ❌ MongoDB connection failed: {e}")
    
    print(f"\n🎉 Production settings test completed!")

if __name__ == "__main__":
    test_production_settings()
