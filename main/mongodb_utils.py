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
        # Categories collection
        self.categories_collection = self.db.get_collection('categories')
        # Orders collection
        self.orders_collection = self.db.get_collection('orders')
        # Payments collection (try both 'payment' and 'payments' to support different naming)
        try:
            self.payments_collection = self.db.get_collection('payments')
        except:
            self.payments_collection = self.db.get_collection('payment')
        # Carts collection
        self.carts_collection = self.db.get_collection('carts')
        # Wishlists collection
        self.wishlists_collection = self.db.get_collection('wishlists')
        # Addresses collection
        self.addresses_collection = self.db.get_collection('addresses')
        # Sliders collection
        self.sliders_collection = self.db.get_collection('sliders')
        # FAQs collection
        self.faqs_collection = self.db.get_collection('faqs')
    
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
            # Hash password if it's being updated
            if 'password' in update_data:
                password = update_data['password'].encode('utf-8')
                hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
                update_data['password'] = hashed_password.decode('utf-8')
            
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
        # First image is the main image
        main_image = ''
        if images:
            main_image = images[0]
            # URL-encode spaces in local file paths if needed
            if not main_image.startswith('http://') and not main_image.startswith('https://'):
                main_image = main_image.replace(' ', '%20') if ' ' in main_image else main_image
        # Normalize category_id to string for JSON serialization
        raw_category_id = product_doc.get('category_id')
        if isinstance(raw_category_id, ObjectId):
            category_id_str = str(raw_category_id)
        else:
            category_id_str = raw_category_id if (isinstance(raw_category_id, str) or raw_category_id is None) else str(raw_category_id)
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
            'category_id': category_id_str,
            'tags': product_doc.get('tags') or [],
            'images': images,
            'main_image': main_image,
            'created_at': product_doc.get('created_at'),
            'updated_at': product_doc.get('updated_at'),
        }

    def list_products(self, *, category: str | None = None, search: str | None = None, max_price: str | None = None, sort_by: str | None = None, date_from: str | None = None, date_to: str | None = None, page: int | None = None, page_size: int = 12):
        """Return a list of products with optional filtering and basic pagination."""
        from datetime import datetime
        
        query = {}
        
        # Category filter - supports hierarchical filtering (parent includes children)
        category_ids_list = []
        if category:
            # Handle both ObjectId and string inputs
            category_str = None
            if isinstance(category, ObjectId):
                category_str = str(category)
            elif isinstance(category, str):
                category_str = category.strip()
            
            if category_str:
                try:
                    category_id_obj = ObjectId(category_str)
                    # Get all child categories (recursively) for hierarchical filtering
                    all_category_ids = [category_id_obj]
                
                    # Recursive function to get all child categories
                    def get_child_categories(parent_obj_id):
                        child_categories = self.categories_collection.find({'parent_id': parent_obj_id})
                        child_ids = []
                        for child in child_categories:
                            child_id = child.get('_id')
                            if child_id:
                                child_ids.append(child_id)
                                # Recursively get grandchildren
                                child_ids.extend(get_child_categories(child_id))
                        return child_ids
                
                    # Get all child categories
                    child_ids = get_child_categories(category_id_obj)
                    if child_ids:
                        all_category_ids.extend(child_ids)
                    
                    # Store category IDs for later use in query building
                    category_ids_list = all_category_ids
                except Exception:
                    # If ObjectId conversion fails, skip category filter
                    pass
        
        # Search filter (only if search is provided and not empty)
        search_pattern = None
        if search and search.strip():
            search_pattern = search.strip()
            
        # Price filter (only if max_price is provided and not empty)
        max_price_val = None
        if max_price and max_price.strip() and max_price.strip().isdigit():
            max_price_val = float(max_price.strip())
        
        # Date filters (work independently - can use date_from alone, date_to alone, or both)
        date_query = {}
        if date_from and date_from.strip():
            try:
                date_from_obj = datetime.strptime(date_from.strip(), '%Y-%m-%d')
                date_query['$gte'] = date_from_obj
            except (ValueError, TypeError):
                pass
        if date_to and date_to.strip():
            try:
                date_to_obj = datetime.strptime(date_to.strip(), '%Y-%m-%d')
                # Add 23:59:59 to include the entire day
                date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
                date_query['$lte'] = date_to_obj
            except (ValueError, TypeError):
                pass
        
        # Build MongoDB query - combine all filters properly
        # If we have category filter with hierarchical support, we need to use $or for category matching
        # and combine it with other filters using $and
        if category_ids_list:
            # Build category match conditions (support ObjectId, string ObjectId, and legacy category field)
            category_conditions = [
                {'category_id': {'$in': category_ids_list}},  # ObjectId format
            ]
            # Also add string versions for compatibility
            category_str_ids = [str(cid) for cid in category_ids_list]
            category_conditions.append({'category_id': {'$in': category_str_ids}})  # String ObjectId format
            category_conditions.append({'category': {'$in': category_str_ids}})  # Legacy category field
            
            # Combine category conditions
            category_filter = {'$or': category_conditions}
            
            # Combine with other filters using $and if we have multiple conditions
            and_conditions = [category_filter]
            
            if search_pattern:
                and_conditions.append({'name': {'$regex': search_pattern, '$options': 'i'}})
            
            if max_price_val is not None:
                and_conditions.append({'price': {'$lte': max_price_val}})
            
            if date_query:
                and_conditions.append({'created_at': date_query})
            
            if len(and_conditions) > 1:
                query = {'$and': and_conditions}
            else:
                query = and_conditions[0]
        else:
            # No category filter, build simple query
            if search_pattern:
                query['name'] = {'$regex': search_pattern, '$options': 'i'}
            
            if max_price_val is not None:
                query['price'] = {'$lte': max_price_val}
            
            if date_query:
                query['created_at'] = date_query

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
    
    # --------------------
    # Product Management (CRUD)
    # --------------------
    def create_product(self, product_data):
        """Create a new product in MongoDB"""
        # Add timestamps
        product_data['created_at'] = datetime.utcnow()
        product_data['updated_at'] = datetime.utcnow()
        
        # Convert category_id to ObjectId if it's provided as string
        if 'category_id' in product_data and product_data['category_id']:
            if isinstance(product_data['category_id'], str):
                try:
                    product_data['category_id'] = ObjectId(product_data['category_id'])
                except:
                    product_data['category_id'] = None
            elif product_data['category_id'] is None or product_data['category_id'] == '':
                product_data['category_id'] = None
        else:
            product_data['category_id'] = None
        
        # Set default values
        product_data.setdefault('is_available', True)
        product_data.setdefault('quantity', 0)
        product_data.setdefault('tags', [])
        product_data.setdefault('images', [])
        
        result = self.products_collection.insert_one(product_data)
        return str(result.inserted_id)
    
    def update_product(self, product_id: str, update_data):
        """Update product in MongoDB"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            # Convert category_id to ObjectId if it's provided as string
            if 'category_id' in update_data:
                if isinstance(update_data['category_id'], str) and update_data['category_id'].strip():
                    try:
                        update_data['category_id'] = ObjectId(update_data['category_id'].strip())
                    except:
                        update_data['category_id'] = None
                elif not update_data['category_id'] or update_data['category_id'] == '':
                    update_data['category_id'] = None
            
            object_id = ObjectId(product_id)
            result = self.products_collection.update_one(
                {'_id': object_id},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete_product(self, product_id: str):
        """Delete product from MongoDB"""
        try:
            object_id = ObjectId(product_id)
            result = self.products_collection.delete_one({'_id': object_id})
            return result.deleted_count > 0
        except Exception:
            return False
    
    # --------------------
    # Category helpers
    # --------------------
    @staticmethod
    def _format_category_doc(category_doc):
        """Map a MongoDB category document to a template-friendly dict."""
        if not category_doc:
            return None
        return {
            'id': str(category_doc.get('_id')),
            'name': category_doc.get('name', ''),
            'slug': category_doc.get('slug', ''),
            'description': category_doc.get('description', ''),
            'image': category_doc.get('image', ''),
            'parent_id': str(category_doc.get('parent_id')) if category_doc.get('parent_id') else None,
            'is_active': category_doc.get('is_active', True),
            'sort_order': category_doc.get('sort_order', 0),
            'created_at': category_doc.get('created_at'),
            'updated_at': category_doc.get('updated_at'),
        }
    
    def list_categories(self, parent_id: str | None = None, is_active: bool | None = None, top_level_only: bool = False):
        """List all categories with optional filtering"""
        query = {}
        
        # Handle parent_id filtering
        if parent_id is not None and parent_id != '':
            try:
                query['parent_id'] = ObjectId(parent_id)
            except:
                pass
        elif top_level_only:
            query['parent_id'] = None  # Top-level categories only
        
        # Handle is_active filtering
        if is_active is not None:
            query['is_active'] = is_active
        
        cursor = self.categories_collection.find(query).sort('sort_order', 1)
        return [self._format_category_doc(doc) for doc in cursor]
    
    def get_category_by_id(self, category_id: str):
        """Get category by ID"""
        try:
            doc = self.categories_collection.find_one({'_id': ObjectId(category_id)})
        except Exception:
            doc = None
        return self._format_category_doc(doc)
    
    def get_category_by_slug(self, slug: str):
        """Get category by slug"""
        doc = self.categories_collection.find_one({'slug': slug})
        return self._format_category_doc(doc)
    
    # --------------------
    # Category Management (CRUD)
    # --------------------
    def create_category(self, category_data):
        """Create a new category in MongoDB"""
        # Add timestamps
        category_data['created_at'] = datetime.utcnow()
        category_data['updated_at'] = datetime.utcnow()
        
        # Handle parent_id conversion
        if category_data.get('parent_id'):
            try:
                category_data['parent_id'] = ObjectId(category_data['parent_id'])
            except:
                category_data['parent_id'] = None
        else:
            category_data['parent_id'] = None
        
        # Set default values
        category_data.setdefault('is_active', True)
        category_data.setdefault('sort_order', 0)
        category_data.setdefault('image', '')
        category_data.setdefault('description', '')
        
        result = self.categories_collection.insert_one(category_data)
        return str(result.inserted_id)
    
    def update_category(self, category_id: str, update_data):
        """Update category in MongoDB"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            # Handle parent_id conversion
            if 'parent_id' in update_data:
                if update_data['parent_id']:
                    try:
                        update_data['parent_id'] = ObjectId(update_data['parent_id'])
                    except:
                        update_data['parent_id'] = None
                else:
                    update_data['parent_id'] = None
            
            object_id = ObjectId(category_id)
            result = self.categories_collection.update_one(
                {'_id': object_id},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete_category(self, category_id: str):
        """Delete category from MongoDB"""
        try:
            object_id = ObjectId(category_id)
            result = self.categories_collection.delete_one({'_id': object_id})
            return result.deleted_count > 0
        except Exception:
            return False

    # --------------------
    # Cart helpers
    # --------------------
    def get_user_cart(self, user_id: str):
        """Get user's cart from MongoDB"""
        try:
            # Convert user_id to ObjectId if it's a string
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    # If it's not a valid ObjectId, try to find by username
                    user = self.get_user_by_username(user_id)
                    if user:
                        user_id = user.get('_id')
                    else:
                        return None
            
            cart = self.carts_collection.find_one({'user_id': user_id})
            return cart
        except Exception as e:
            print(f"Error getting user cart: {e}")
            return None
    
    def save_user_cart(self, user_id: str, cart_data: list):
        """Save or update user's cart in MongoDB"""
        try:
            # Convert user_id to ObjectId if it's a string
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    # If it's not a valid ObjectId, try to find by username
                    user = self.get_user_by_username(user_id)
                    if user:
                        user_id = user.get('_id')
                    else:
                        return False
            
            # Upsert cart (update if exists, create if not)
            result = self.carts_collection.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'cart_data': cart_data,
                        'updated_at': datetime.utcnow()
                    },
                    '$setOnInsert': {
                        'created_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error saving user cart: {e}")
            return False
    
    def clear_user_cart(self, user_id: str):
        """Clear user's cart in MongoDB"""
        try:
            # Convert user_id to ObjectId if it's a string
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    # If it's not a valid ObjectId, try to find by username
                    user = self.get_user_by_username(user_id)
                    if user:
                        user_id = user.get('_id')
                    else:
                        return False
            
            result = self.carts_collection.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'cart_data': [],
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            print(f"Error clearing user cart: {e}")
            return False

    # --------------------
    # Wishlist helpers
    # --------------------
    def get_user_wishlist(self, user_id: str):
        """Get user's wishlist from MongoDB"""
        try:
            # Convert user_id to ObjectId if it's a string
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    # If it's not a valid ObjectId, try to find by username
                    user = self.get_user_by_username(user_id)
                    if user:
                        user_id = user.get('_id')
                    else:
                        return []
            
            wishlist = self.wishlists_collection.find_one({'user_id': user_id})
            if wishlist and wishlist.get('items'):
                return wishlist.get('items', [])
            return []
        except Exception as e:
            print(f"Error getting user wishlist: {e}")
            return []
    
    def add_to_wishlist(self, user_id: str, product_id: str):
        """Add product to user's wishlist"""
        try:
            # Convert user_id to ObjectId
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    user = self.get_user_by_username(user_id)
                    if user:
                        user_id = user.get('_id')
                    else:
                        return False
            
            # Convert product_id to ObjectId
            if isinstance(product_id, str):
                try:
                    product_id = ObjectId(product_id)
                except:
                    return False
            
            # Get current wishlist
            wishlist = self.wishlists_collection.find_one({'user_id': user_id})
            
            if wishlist:
                items = wishlist.get('items', [])
                # Check if product already in wishlist
                if product_id not in items:
                    items.append(product_id)
                    self.wishlists_collection.update_one(
                        {'user_id': user_id},
                        {
                            '$set': {
                                'items': items,
                                'updated_at': datetime.utcnow()
                            }
                        }
                    )
                    return True
                return False  # Already in wishlist
            else:
                # Create new wishlist
                self.wishlists_collection.insert_one({
                    'user_id': user_id,
                    'items': [product_id],
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                return True
        except Exception as e:
            print(f"Error adding to wishlist: {e}")
            return False
    
    def remove_from_wishlist(self, user_id: str, product_id: str):
        """Remove product from user's wishlist"""
        try:
            # Convert user_id to ObjectId
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    user = self.get_user_by_username(user_id)
                    if user:
                        user_id = user.get('_id')
                    else:
                        return False
            
            # Convert product_id to ObjectId
            if isinstance(product_id, str):
                try:
                    product_id = ObjectId(product_id)
                except:
                    return False
            
            wishlist = self.wishlists_collection.find_one({'user_id': user_id})
            if wishlist:
                items = wishlist.get('items', [])
                if product_id in items:
                    items.remove(product_id)
                    self.wishlists_collection.update_one(
                        {'user_id': user_id},
                        {
                            '$set': {
                                'items': items,
                                'updated_at': datetime.utcnow()
                            }
                        }
                    )
                    return True
            return False
        except Exception as e:
            print(f"Error removing from wishlist: {e}")
            return False
    
    def is_in_wishlist(self, user_id: str, product_id: str):
        """Check if product is in user's wishlist"""
        try:
            # Convert user_id to ObjectId
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    user = self.get_user_by_username(user_id)
                    if user:
                        user_id = user.get('_id')
                    else:
                        return False
            
            # Convert product_id to ObjectId
            if isinstance(product_id, str):
                try:
                    product_id = ObjectId(product_id)
                except:
                    return False
            
            wishlist = self.wishlists_collection.find_one({'user_id': user_id})
            if wishlist:
                items = wishlist.get('items', [])
                return product_id in items
            return False
        except Exception as e:
            print(f"Error checking wishlist: {e}")
            return False

    # --------------------
    # Order helpers
    # --------------------
    def create_order(self, order_data):
        """Create a new order in MongoDB"""
        try:
            # Convert user_id to ObjectId if provided
            if 'user_id' in order_data and order_data['user_id']:
                if isinstance(order_data['user_id'], str):
                    try:
                        order_data['user_id'] = ObjectId(order_data['user_id'])
                    except:
                        user = self.get_user_by_username(order_data['user_id'])
                        if user:
                            order_data['user_id'] = user.get('_id')
                        else:
                            return None
            
            # Generate order number if not provided
            if 'order_number' not in order_data or not order_data.get('order_number'):
                # Generate unique order number (e.g., ORD-YYYYMMDD-HHMMSS-XXXX)
                timestamp = datetime.utcnow()
                order_data['order_number'] = f"ORD-{timestamp.strftime('%Y%m%d')}-{timestamp.strftime('%H%M%S')}-{str(timestamp.microsecond)[:4]}"
            
            # Set default values
            order_data.setdefault('status', 'pending')
            order_data.setdefault('payment_status', 'pending')
            order_data['created_at'] = datetime.utcnow()
            order_data['updated_at'] = datetime.utcnow()
            
            result = self.orders_collection.insert_one(order_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating order: {e}")
            return None
    
    def get_user_orders(self, user_id: str, limit: int = None):
        """Get orders for a specific user"""
        try:
            # Convert user_id to ObjectId
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    user = self.get_user_by_username(user_id)
                    if user:
                        user_id = user.get('_id')
                    else:
                        return []
            
            query = {'user_id': user_id}
            cursor = self.orders_collection.find(query).sort('created_at', -1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            orders = []
            for doc in cursor:
                order = {
                    'id': str(doc.get('_id')),
                    'order_number': doc.get('order_number', ''),
                    'user_id': str(doc.get('user_id')) if doc.get('user_id') else None,
                    'items': doc.get('items', []),
                    'subtotal': float(doc.get('subtotal', 0)),
                    'shipping_cost': float(doc.get('shipping_cost', 0)),
                    'tax_amount': float(doc.get('tax_amount', 0)),
                    'total_amount': float(doc.get('total_amount', 0)),
                    'status': doc.get('status', 'pending'),
                    'payment_status': doc.get('payment_status', 'pending'),
                    'shipping_address': doc.get('shipping_address', {}),
                    'payment_method': doc.get('payment_method', ''),
                    'notes': doc.get('notes', ''),
                    'created_at': doc.get('created_at'),
                    'updated_at': doc.get('updated_at'),
                }
                orders.append(order)
            
            return orders
        except Exception as e:
            print(f"Error getting user orders: {e}")
            return []
    
    def list_orders(self, page=1, page_size=10, status=None, date_from=None, date_to=None, user_id=None):
        """List all orders with pagination and filters"""
        try:
            query = {}
            
            # Apply status filter
            if status:
                query['status'] = status
            
            # Filter by user
            if user_id:
                query['user_id'] = user_id

            # Apply date filters
            if date_from or date_to:
                date_query = {}
                if date_from:
                    try:
                        from datetime import datetime
                        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                        date_query['$gte'] = date_from_obj
                    except:
                        pass
                if date_to:
                    try:
                        from datetime import datetime
                        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                        # Include the entire day
                        from datetime import timedelta
                        date_to_obj = date_to_obj + timedelta(days=1)
                        date_query['$lt'] = date_to_obj
                    except:
                        pass
                if date_query:
                    query['created_at'] = date_query
            
            # Get total count
            total = self.orders_collection.count_documents(query)
            
            # Apply pagination
            skip = (page - 1) * page_size
            cursor = self.orders_collection.find(query).sort('created_at', -1).skip(skip).limit(page_size)
            
            orders = []
            for doc in cursor:
                order = {
                    'id': str(doc.get('_id')),
                    'order_number': doc.get('order_number', ''),
                    'user_id': str(doc.get('user_id')) if doc.get('user_id') else None,
                    'items': doc.get('items', []),
                    'subtotal': float(doc.get('subtotal', 0)),
                    'shipping_cost': float(doc.get('shipping_cost', 0)),
                    'tax_amount': float(doc.get('tax_amount', 0)),
                    'total_amount': float(doc.get('total_amount', 0)),
                    'status': doc.get('status', 'pending'),
                    'payment_status': doc.get('payment_status', 'pending'),
                    'shipping_address': doc.get('shipping_address', {}),
                    'payment_method': doc.get('payment_method', ''),
                    'notes': doc.get('notes', ''),
                    'created_at': doc.get('created_at'),
                    'updated_at': doc.get('updated_at'),
                }
                orders.append(order)
            
            return {
                'items': orders,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            print(f"Error listing orders: {e}")
            import traceback
            print(traceback.format_exc())
            return {
                'items': [],
                'total': 0,
                'page': page,
                'page_size': page_size
            }
    
    def list_payments(self, page=1, page_size=10, status=None, date_from=None, date_to=None, order_id=None, user_id=None):
        """List all payments with pagination and filters"""
        try:
            query = {}
            
            # Apply status filter
            if status:
                query['status'] = status
            
            # Filter by order and user
            if order_id:
                query['order_id'] = order_id
            if user_id:
                query['user_id'] = user_id

            # Apply date filters
            if date_from or date_to:
                date_query = {}
                if date_from:
                    try:
                        from datetime import datetime
                        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                        date_query['$gte'] = date_from_obj
                    except:
                        pass
                if date_to:
                    try:
                        from datetime import datetime
                        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                        # Include the entire day
                        from datetime import timedelta
                        date_to_obj = date_to_obj + timedelta(days=1)
                        date_query['$lt'] = date_to_obj
                    except:
                        pass
                if date_query:
                    query['created_at'] = date_query
            
            # Get total count
            total = self.payments_collection.count_documents(query)
            
            # Apply pagination
            skip = (page - 1) * page_size
            cursor = self.payments_collection.find(query).sort('created_at', -1).skip(skip).limit(page_size)
            
            payments = []
            for doc in cursor:
                payment = {
                    'id': str(doc.get('_id')),
                    'transaction_id': doc.get('transaction_id', ''),
                    'order_id': str(doc.get('order_id')) if doc.get('order_id') else None,
                    'user_id': str(doc.get('user_id')) if doc.get('user_id') else None,
                    'amount': float(doc.get('amount', 0)),
                    'currency': doc.get('currency', 'USD'),
                    'payment_method': doc.get('payment_method', ''),
                    'status': doc.get('status', 'pending'),
                    'payment_details': doc.get('payment_details', {}),
                    'created_at': doc.get('created_at'),
                    'updated_at': doc.get('updated_at'),
                }
                payments.append(payment)
            
            return {
                'items': payments,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            print(f"Error listing payments: {e}")
            import traceback
            print(traceback.format_exc())
            return {
                'items': [],
                'total': 0,
                'page': page,
                'page_size': page_size
            }
    
    # --------------------
    # Payment helpers
    # --------------------
    def create_payment(self, payment_data):
        """Create a new payment record in MongoDB"""
        try:
            # Convert order_id and user_id to ObjectId if provided
            if 'order_id' in payment_data and payment_data['order_id']:
                if isinstance(payment_data['order_id'], str):
                    try:
                        payment_data['order_id'] = ObjectId(payment_data['order_id'])
                    except:
                        return None
            
            if 'user_id' in payment_data and payment_data['user_id']:
                if isinstance(payment_data['user_id'], str):
                    try:
                        payment_data['user_id'] = ObjectId(payment_data['user_id'])
                    except:
                        user = self.get_user_by_username(payment_data['user_id'])
                        if user:
                            payment_data['user_id'] = user.get('_id')
                        else:
                            return None
            
            # Generate transaction ID if not provided
            if 'transaction_id' not in payment_data or not payment_data.get('transaction_id'):
                timestamp = datetime.utcnow()
                payment_data['transaction_id'] = f"TXN-{timestamp.strftime('%Y%m%d%H%M%S')}-{str(timestamp.microsecond)[:4]}"
            
            # Set default values
            payment_data.setdefault('status', 'pending')
            payment_data['created_at'] = datetime.utcnow()
            payment_data['updated_at'] = datetime.utcnow()
            
            print(f"DEBUG: Creating payment with data: order_id={payment_data.get('order_id')}, user_id={payment_data.get('user_id')}, amount={payment_data.get('amount')}")
            
            result = self.payments_collection.insert_one(payment_data)
            payment_inserted_id = str(result.inserted_id)
            print(f"DEBUG: Payment created successfully with ID: {payment_inserted_id}")
            return payment_inserted_id
        except Exception as e:
            print(f"Error creating payment: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def update_payment_status(self, payment_id: str, status: str, transaction_details: dict = None):
        """Update payment status"""
        try:
            payment_id_obj = ObjectId(payment_id)
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow()
            }
            
            if transaction_details:
                # Merge transaction_details into payment_details field
                payment_doc = self.payments_collection.find_one({'_id': payment_id_obj})
                if payment_doc:
                    payment_details = payment_doc.get('payment_details', {})
                    payment_details.update(transaction_details)
                    update_data['payment_details'] = payment_details
                else:
                    update_data['payment_details'] = transaction_details
            
            result = self.payments_collection.update_one(
                {'_id': payment_id_obj},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating payment status: {e}")
            return False
    
    def update_order_status(self, order_id: str, status: str, payment_status: str = None):
        """Update order status and optionally payment_status"""
        try:
            order_id_obj = ObjectId(order_id)
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow()
            }
            
            # If payment_status is provided, update it as well
            if payment_status is not None:
                update_data['payment_status'] = payment_status
            
            result = self.orders_collection.update_one(
                {'_id': order_id_obj},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False
    
    def update_order(self, order_id: str, update_data: dict):
        """Update order fields"""
        try:
            order_id_obj = ObjectId(order_id)
            update_data['updated_at'] = datetime.utcnow()
            result = self.orders_collection.update_one(
                {'_id': order_id_obj},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating order: {e}")
            return False
    
    def get_order_by_id(self, order_id: str):
        """Get order by ID"""
        try:
            order_id_obj = ObjectId(order_id)
            doc = self.orders_collection.find_one({'_id': order_id_obj})
            if doc:
                return {
                    'id': str(doc.get('_id')),
                    'order_number': doc.get('order_number', ''),
                    'user_id': str(doc.get('user_id')) if doc.get('user_id') else None,
                    'items': doc.get('items', []),
                    'subtotal': float(doc.get('subtotal', 0)),
                    'shipping_cost': float(doc.get('shipping_cost', 0)),
                    'tax_amount': float(doc.get('tax_amount', 0)),
                    'total_amount': float(doc.get('total_amount', 0)),
                    'status': doc.get('status', 'pending'),
                    'payment_status': doc.get('payment_status', 'pending'),
                    'shipping_address': doc.get('shipping_address', {}),
                    'payment_method': doc.get('payment_method', ''),
                    'notes': doc.get('notes', ''),
                    'created_at': doc.get('created_at'),
                    'updated_at': doc.get('updated_at'),
                }
            return None
        except Exception as e:
            print(f"Error getting order: {e}")
            return None
    
    # --------------------
    # Address Management Methods
    # --------------------
    def create_address(self, address_data):
        """Create a new address in MongoDB addresses collection"""
        try:
            # Convert user_id to ObjectId if provided as string
            if 'user_id' in address_data and address_data['user_id']:
                if isinstance(address_data['user_id'], str):
                    try:
                        address_data['user_id'] = ObjectId(address_data['user_id'])
                    except:
                        return None
            
            # Add timestamps
            address_data['created_at'] = datetime.utcnow()
            address_data['updated_at'] = datetime.utcnow()
            
            # If setting as default, unset other defaults for this user
            if address_data.get('is_default', False):
                self.addresses_collection.update_many(
                    {'user_id': address_data.get('user_id'), 'is_default': True},
                    {'$set': {'is_default': False}}
                )
            
            result = self.addresses_collection.insert_one(address_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating address: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def get_user_addresses(self, user_id: str):
        """Get all addresses for a user"""
        try:
            user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
            addresses = list(self.addresses_collection.find(
                {'user_id': user_id_obj},
                sort=[('is_default', -1), ('created_at', -1)]
            ))
            
            # Convert ObjectId to string and remove _id to avoid template access issues
            for addr in addresses:
                addr['id'] = str(addr['_id'])
                # Remove _id from dict to prevent Django template from accessing it
                if '_id' in addr:
                    del addr['_id']
                # Convert user_id to string if it's ObjectId
                if isinstance(addr.get('user_id'), ObjectId):
                    addr['user_id'] = str(addr['user_id'])
            
            return addresses
        except Exception as e:
            print(f"Error getting user addresses: {e}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def list_sliders(self, status: str = 'active'):
        """Get sliders from MongoDB"""
        try:
            query = {}
            if status:
                query['status'] = status
            
            sliders = list(self.sliders_collection.find(query).sort('order', 1))
            
            # Convert ObjectId to string
            for slider in sliders:
                slider['id'] = str(slider['_id'])
                if '_id' in slider:
                    del slider['_id']
                # Convert datetime to string if needed
                if 'created_at' in slider and isinstance(slider['created_at'], datetime):
                    slider['created_at'] = slider['created_at'].isoformat()
                if 'updated_at' in slider and isinstance(slider['updated_at'], datetime):
                    slider['updated_at'] = slider['updated_at'].isoformat()
            
            return sliders
        except Exception as e:
            print(f"Error getting sliders from MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_slider_by_id(self, slider_id: str):
        """Get slider by ID from MongoDB"""
        try:
            slider_id_obj = ObjectId(slider_id)
            slider = self.sliders_collection.find_one({'_id': slider_id_obj})
            if slider:
                slider['id'] = str(slider['_id'])
                if '_id' in slider:
                    del slider['_id']
                # Convert datetime to string if needed
                if 'created_at' in slider and isinstance(slider['created_at'], datetime):
                    slider['created_at'] = slider['created_at'].isoformat()
                if 'updated_at' in slider and isinstance(slider['updated_at'], datetime):
                    slider['updated_at'] = slider['updated_at'].isoformat()
            return slider
        except Exception as e:
            print(f"Error getting slider by ID from MongoDB: {e}")
            return None
    
    def create_slider(self, slider_data: dict):
        """Create a new slider in MongoDB"""
        try:
            # Add timestamps
            slider_data['created_at'] = datetime.utcnow()
            slider_data['updated_at'] = datetime.utcnow()
            
            # Set default values
            slider_data.setdefault('status', 'active')
            slider_data.setdefault('order', 0)
            
            # If order is provided, check if it conflicts and adjust
            if 'order' in slider_data:
                order = slider_data['order']
                # Shift existing sliders with same or higher order
                self.sliders_collection.update_many(
                    {'order': {'$gte': order}},
                    {'$inc': {'order': 1}}
                )
            
            result = self.sliders_collection.insert_one(slider_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating slider in MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_slider(self, slider_id: str, update_data: dict):
        """Update slider in MongoDB"""
        try:
            slider_id_obj = ObjectId(slider_id)
            update_data['updated_at'] = datetime.utcnow()
            
            # If order is being changed, handle reordering
            if 'order' in update_data:
                # Get current slider
                current_slider = self.sliders_collection.find_one({'_id': slider_id_obj})
                if current_slider:
                    old_order = current_slider.get('order', 0)
                    new_order = update_data['order']
                    
                    if old_order != new_order:
                        # Shift other sliders
                        if new_order > old_order:
                            # Moving to higher order - shift sliders between old and new down
                            self.sliders_collection.update_many(
                                {'order': {'$gt': old_order, '$lte': new_order}, '_id': {'$ne': slider_id_obj}},
                                {'$inc': {'order': -1}}
                            )
                        else:
                            # Moving to lower order - shift sliders between new and old up
                            self.sliders_collection.update_many(
                                {'order': {'$gte': new_order, '$lt': old_order}, '_id': {'$ne': slider_id_obj}},
                                {'$inc': {'order': 1}}
                            )
            
            result = self.sliders_collection.update_one(
                {'_id': slider_id_obj},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating slider in MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_slider(self, slider_id: str):
        """Delete slider from MongoDB"""
        try:
            slider_id_obj = ObjectId(slider_id)
            # Get slider to get its order
            slider = self.sliders_collection.find_one({'_id': slider_id_obj})
            if slider:
                order = slider.get('order', 0)
                # Delete the slider
                result = self.sliders_collection.delete_one({'_id': slider_id_obj})
                if result.deleted_count > 0:
                    # Reorder remaining sliders
                    self.sliders_collection.update_many(
                        {'order': {'$gt': order}},
                        {'$inc': {'order': -1}}
                    )
                    return True
            return False
        except Exception as e:
            print(f"Error deleting slider from MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def toggle_slider_status(self, slider_id: str):
        """Toggle slider status (active/inactive)"""
        try:
            slider_id_obj = ObjectId(slider_id)
            slider = self.sliders_collection.find_one({'_id': slider_id_obj})
            if slider:
                new_status = 'inactive' if slider.get('status') == 'active' else 'active'
                result = self.sliders_collection.update_one(
                    {'_id': slider_id_obj},
                    {'$set': {'status': new_status, 'updated_at': datetime.utcnow()}}
                )
                return new_status if result.modified_count > 0 else None
            return None
        except Exception as e:
            print(f"Error toggling slider status in MongoDB: {e}")
            return None
    
    def reorder_sliders(self, items: list):
        """Reorder sliders based on provided items list"""
        try:
            # First, update all sliders to temporary high order numbers to avoid conflicts
            temp_start = 10000
            for i, item in enumerate(items):
                slider_id = item.get('id')
                if slider_id:
                    try:
                        slider_id_obj = ObjectId(slider_id)
                        self.sliders_collection.update_one(
                            {'_id': slider_id_obj},
                            {'$set': {'order': temp_start + i}}
                        )
                    except:
                        continue
            
            # Then update to final order numbers
            for item in items:
                slider_id = item.get('id')
                final_order = item.get('order')
                if slider_id and final_order is not None:
                    try:
                        slider_id_obj = ObjectId(slider_id)
                        self.sliders_collection.update_one(
                            {'_id': slider_id_obj},
                            {'$set': {'order': final_order, 'updated_at': datetime.utcnow()}}
                        )
                    except:
                        continue
            
            return True
        except Exception as e:
            print(f"Error reordering sliders in MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_next_slider_order(self):
        """Get the next available order number for sliders"""
        try:
            max_order = self.sliders_collection.find_one(sort=[('order', -1)])
            if max_order and 'order' in max_order:
                return max_order['order'] + 1
            return 1
        except:
            return 1
    
    # FAQ Methods
    def list_faqs(self, category: str = None, is_active: bool = True):
        """Get FAQs from MongoDB"""
        try:
            query = {}
            if is_active is not None:
                query['is_active'] = is_active
            if category:
                query['category'] = category
            
            faqs = list(self.faqs_collection.find(query).sort('order', 1))
            
            # Convert ObjectId to string
            for faq in faqs:
                faq['id'] = str(faq['_id'])
                if '_id' in faq:
                    del faq['_id']
                # Convert datetime to string if needed
                if 'created_at' in faq and isinstance(faq['created_at'], datetime):
                    faq['created_at'] = faq['created_at'].isoformat()
                if 'updated_at' in faq and isinstance(faq['updated_at'], datetime):
                    faq['updated_at'] = faq['updated_at'].isoformat()
            
            return faqs
        except Exception as e:
            print(f"Error getting FAQs from MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_faq_by_id(self, faq_id: str):
        """Get FAQ by ID from MongoDB"""
        try:
            faq_id_obj = ObjectId(faq_id)
            faq = self.faqs_collection.find_one({'_id': faq_id_obj})
            if faq:
                faq['id'] = str(faq['_id'])
                if '_id' in faq:
                    del faq['_id']
                # Convert datetime to string if needed
                if 'created_at' in faq and isinstance(faq['created_at'], datetime):
                    faq['created_at'] = faq['created_at'].isoformat()
                if 'updated_at' in faq and isinstance(faq['updated_at'], datetime):
                    faq['updated_at'] = faq['updated_at'].isoformat()
            return faq
        except Exception as e:
            print(f"Error getting FAQ by ID from MongoDB: {e}")
            return None
    
    def search_faqs(self, query: str, is_active: bool = True):
        """Search FAQs by question or answer"""
        try:
            search_query = {
                'is_active': is_active,
                '$or': [
                    {'question': {'$regex': query, '$options': 'i'}},
                    {'answer': {'$regex': query, '$options': 'i'}},
                    {'keywords': {'$regex': query, '$options': 'i'}}
                ]
            }
            
            faqs = list(self.faqs_collection.find(search_query).sort('order', 1))
            
            # Convert ObjectId to string
            for faq in faqs:
                faq['id'] = str(faq['_id'])
                if '_id' in faq:
                    del faq['_id']
                # Convert datetime to string if needed
                if 'created_at' in faq and isinstance(faq['created_at'], datetime):
                    faq['created_at'] = faq['created_at'].isoformat()
                if 'updated_at' in faq and isinstance(faq['updated_at'], datetime):
                    faq['updated_at'] = faq['updated_at'].isoformat()
            
            return faqs
        except Exception as e:
            print(f"Error searching FAQs from MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def create_faq(self, faq_data: dict):
        """Create a new FAQ in MongoDB"""
        try:
            # Add timestamps
            faq_data['created_at'] = datetime.utcnow()
            faq_data['updated_at'] = datetime.utcnow()
            
            # Set default values
            faq_data.setdefault('is_active', True)
            faq_data.setdefault('order', 0)
            faq_data.setdefault('category', 'general')
            faq_data.setdefault('keywords', [])
            
            result = self.faqs_collection.insert_one(faq_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating FAQ in MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_faq(self, faq_id: str, update_data: dict):
        """Update FAQ in MongoDB"""
        try:
            faq_id_obj = ObjectId(faq_id)
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.faqs_collection.update_one(
                {'_id': faq_id_obj},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating FAQ in MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_faq(self, faq_id: str):
        """Delete FAQ from MongoDB"""
        try:
            faq_id_obj = ObjectId(faq_id)
            result = self.faqs_collection.delete_one({'_id': faq_id_obj})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting FAQ from MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_address_by_id(self, address_id: str):
        """Get address by ID"""
        try:
            address_id_obj = ObjectId(address_id)
            doc = self.addresses_collection.find_one({'_id': address_id_obj})
            if doc:
                doc['id'] = str(doc['_id'])
                # Remove _id from dict to prevent Django template from accessing it
                if '_id' in doc:
                    del doc['_id']
                # Convert user_id to string if it's ObjectId
                if isinstance(doc.get('user_id'), ObjectId):
                    doc['user_id'] = str(doc['user_id'])
            return doc
        except Exception as e:
            print(f"Error getting address: {e}")
            return None
    
    def update_address(self, address_id: str, update_data: dict):
        """Update address"""
        try:
            address_id_obj = ObjectId(address_id)
            update_data['updated_at'] = datetime.utcnow()
            
            # If setting as default, unset other defaults for this user
            if update_data.get('is_default', False):
                # Get the address first to find user_id
                address = self.addresses_collection.find_one({'_id': address_id_obj})
                if address and address.get('user_id'):
                    self.addresses_collection.update_many(
                        {'user_id': address.get('user_id'), '_id': {'$ne': address_id_obj}, 'is_default': True},
                        {'$set': {'is_default': False}}
                    )
            
            result = self.addresses_collection.update_one(
                {'_id': address_id_obj},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating address: {e}")
            return False
    
    def delete_address(self, address_id: str):
        """Delete address"""
        try:
            address_id_obj = ObjectId(address_id)
            result = self.addresses_collection.delete_one({'_id': address_id_obj})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting address: {e}")
            return False

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()
