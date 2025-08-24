from pymongo import MongoClient
from django.conf import settings
import bcrypt
from datetime import datetime
from bson import ObjectId

class MongoDBManager:
    def __init__(self):
        self.client = MongoClient(
            host=settings.MONGODB_CONFIG['host'],
            port=settings.MONGODB_CONFIG['port']
        )
        self.db = self.client[settings.MONGODB_CONFIG['database']]
        self.users_collection = self.db[settings.MONGODB_CONFIG['collection']]
    
    def create_user(self, user_data):
        """Create a new user in MongoDB"""
        # Hash the password
        if 'password' in user_data:
            password = user_data['password'].encode('utf-8')
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            user_data['password'] = hashed_password.decode('utf-8')
        
        # Add timestamps
        user_data['date_joined'] = datetime.utcnow()
        user_data['last_login'] = None
        
        # Set default values
        user_data.setdefault('is_active', True)
        user_data.setdefault('is_staff', False)
        user_data.setdefault('is_superuser', False)
        
        result = self.users_collection.insert_one(user_data)
        return str(result.inserted_id)
    
    def get_user_by_username(self, username):
        """Get user by username"""
        return self.users_collection.find_one({'username': username})
    
    def get_user_by_email(self, email):
        """Get user by email"""
        return self.users_collection.find_one({'email': email})
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            object_id = ObjectId(user_id)
            return self.users_collection.find_one({'_id': object_id})
        except:
            return None
    
    def update_user(self, user_id, update_data):
        """Update user data"""
        try:
            object_id = ObjectId(user_id)
            result = self.users_collection.update_one(
                {'_id': object_id},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except:
            return False
    
    def delete_user(self, user_id):
        """Delete user"""
        try:
            object_id = ObjectId(user_id)
            result = self.users_collection.delete_one({'_id': object_id})
            return result.deleted_count > 0
        except:
            return False
    
    def get_all_users(self):
        """Get all users"""
        return list(self.users_collection.find())
    
    def verify_password(self, username, password):
        """Verify user password"""
        user = self.get_user_by_username(username)
        if user and 'password' in user:
            stored_password = user['password'].encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), stored_password)
        return False
    
    def update_last_login(self, username):
        """Update user's last login time"""
        return self.users_collection.update_one(
            {'username': username},
            {'$set': {'last_login': datetime.utcnow()}}
        )

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()
