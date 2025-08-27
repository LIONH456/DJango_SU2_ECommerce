from pymongo import MongoClient
from django.conf import settings
import bcrypt
from datetime import datetime
from bson import ObjectId

class MongoDBManager:
    def __init__(self):
        # Use Atlas connection string if available (production), otherwise use local
        if settings.MONGODB_CONFIG.get('atlas_uri'):
            self.client = MongoClient(settings.MONGODB_CONFIG['atlas_uri'])
        else:
            self.client = MongoClient(
                host=settings.MONGODB_CONFIG['host'],
                port=settings.MONGODB_CONFIG['port']
            )
        self.db = self.client[settings.MONGODB_CONFIG['database']]
        self.users_collection = self.db[settings.MONGODB_CONFIG['collection']]
        # Products collection (assumes 'products' collection name)
        self.products_collection = self.db.get_collection('products')
    
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

    # --------------------
    # Product helpers
    # --------------------
    @staticmethod
    def _format_product_doc(product_doc):
        """Map a MongoDB product document to a template-friendly dict."""
        if not product_doc:
            return None
        images = [img for img in (product_doc.get('images') or []) if isinstance(img, str) and img.strip()]
        # Prefer first image without spaces; otherwise URL-encode spaces
        main_image = ''
        if images:
            for img in images:
                if ' ' not in img:
                    main_image = img
                    break
            if not main_image:
                main_image = images[0].replace(' ', '%20')
        return {
            'id': str(product_doc.get('_id')),
            'name': product_doc.get('name', ''),
            'slug': product_doc.get('slug', ''),
            'description': product_doc.get('description', ''),
            'price': product_doc.get('price', 0),
            'compare_price': product_doc.get('compare_price'),
            'sku': product_doc.get('sku', ''),
            'quantity': product_doc.get('quantity', 0),
            'is_available': product_doc.get('is_available', True),
            'category_id': product_doc.get('category_id'),
            'tags': product_doc.get('tags') or [],
            'images': images,
            'main_image': main_image,
            'created_at': product_doc.get('created_at'),
            'updated_at': product_doc.get('updated_at'),
        }

    def list_products(self, *, category: str | None = None, search: str | None = None, max_price: str | None = None, sort_by: str | None = None, page: int | None = None, page_size: int = 12):
        """Return a list of products with optional filtering and basic pagination."""
        query = {}
        
        # Category filter
        if category:
            query['category'] = category
            
        # Search filter
        if search:
            query['name'] = { '$regex': search, '$options': 'i' }
            
        # Price filter
        if max_price and max_price.isdigit():
            query['price'] = { '$lte': float(max_price) }

        cursor = self.products_collection.find(query)
        
        # Sorting
        if sort_by == 'price_low':
            cursor = cursor.sort('price', 1)
        elif sort_by == 'price_high':
            cursor = cursor.sort('price', -1)
        elif sort_by == 'newest':
            cursor = cursor.sort('created_at', -1)
        else:
            cursor = cursor.sort('created_at', -1)  # Default: newest first
            
        total = cursor.count() if hasattr(cursor, 'count') else self.products_collection.count_documents(query)

        if page:
            skip = max(page - 1, 0) * page_size
            cursor = cursor.skip(skip).limit(page_size)

        products = [self._format_product_doc(doc) for doc in cursor]
        return {
            'items': products,
            'total': total,
            'page': page or 1,
            'page_size': page_size,
        }

    def get_product_by_id(self, product_id: str):
        try:
            doc = self.products_collection.find_one({'_id': ObjectId(product_id)})
        except Exception:
            doc = None
        return self._format_product_doc(doc)

    def get_product_by_slug(self, slug: str):
        doc = self.products_collection.find_one({'slug': slug})
        return self._format_product_doc(doc)

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()
