from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from .models import UserAddress, UserProfile, UserSession, UserActivity
from .serializers import (
    UserSerializer, UserCreateSerializer, UserAddressSerializer,
    UserProfileSerializer, UserSessionSerializer, UserActivitySerializer
)
from .product_serializers import ProductSerializer
from .category_serializers import CategorySerializer
from .mongodb_utils import mongodb_manager

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """User registration endpoint"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create user in MongoDB as well
            try:
                user_data = {
                    'username': user.username,
                    'email': user.email,
                    'password': request.data.get('password'),
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone if hasattr(user, 'phone') else '',
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser
                }
                mongodb_manager.create_user(user_data)
            except Exception as e:
                # Log error but don't fail the registration
                pass
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login_api(self, request):
        """User login endpoint"""
        from django.contrib.auth import authenticate
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return Response({
                'success': True,
                'user': UserSerializer(user).data
            })
        return Response({
            'success': False,
            'message': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout_api(self, request):
        """User logout endpoint"""
        logout(request)
        return Response({'success': True, 'message': 'Logged out successfully'})


class UserAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for UserAddress model"""
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProfile model"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's profile"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for UserSession model (read-only)"""
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for UserActivity model (read-only)"""
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user).order_by('-created_at')


# MongoDB Product API Views
class ProductAPIViewSet(viewsets.ViewSet):
    """ViewSet for MongoDB Products - Full CRUD"""
    permission_classes = [IsAuthenticatedOrReadOnly]  # Read public, write requires auth
    
    def get_serializer_class(self):
        return ProductSerializer
    
    def list(self, request):
        """List products with filtering"""
        # Get parameters and strip whitespace, convert to None if empty
        category = request.query_params.get('category', '').strip() or None
        search = (request.query_params.get('q') or request.query_params.get('search') or '').strip() or None
        max_price = request.query_params.get('max_price', '').strip() or None
        sort_by = request.query_params.get('sort', '').strip() or None
        date_from = request.query_params.get('date_from', '').strip() or None
        date_to = request.query_params.get('date_to', '').strip() or None
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        result = mongodb_manager.list_products(
            category=category,
            search=search,
            max_price=max_price,
            sort_by=sort_by,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )
        
        return Response({
            'count': result['total'],
            'next': None if len(result['items']) < page_size else f"?page={page + 1}",
            'previous': None if page == 1 else f"?page={page - 1}",
            'results': result['items']
        })
    
    def create(self, request):
        """Create a new product"""
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return Response(product, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """Get single product by ID"""
        product = mongodb_manager.get_product_by_id(str(pk))
        if not product:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(product)
    
    def update(self, request, pk=None):
        """Update product (full update)"""
        product = mongodb_manager.get_product_by_id(str(pk))
        if not product:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            updated_product = serializer.save()
            return Response(updated_product)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        """Update product (partial update)"""
        product = mongodb_manager.get_product_by_id(str(pk))
        if not product:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            updated_product = serializer.save()
            return Response(updated_product)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete product"""
        product = mongodb_manager.get_product_by_id(str(pk))
        if not product:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        success = mongodb_manager.delete_product(str(pk))
        if success:
            return Response({'message': 'Product deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Failed to delete product'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def featured(self, request):
        """Get featured products"""
        result = mongodb_manager.list_products(
            sort_by='newest',
            page=1,
            page_size=4
        )
        return Response({'results': result['items']})
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def new_arrivals(self, request):
        """Get new arrivals"""
        result = mongodb_manager.list_products(
            sort_by='newest',
            page=1,
            page_size=4
        )
        return Response({'results': result['items']})
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def related(self, request, pk=None):
        """Get related products"""
        product = mongodb_manager.get_product_by_id(str(pk))
        if not product:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        related = []
        if product.get('category_id'):
            rel_result = mongodb_manager.list_products(
                category=product['category_id'],
                page=1,
                page_size=4
            )
            related = [p for p in rel_result['items'] if p['id'] != product['id']][:4]
        
        return Response({'results': related})


# MongoDB Order API Views
class OrderAPIViewSet(viewsets.ViewSet):
    """ViewSet for MongoDB Orders - Read Only"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        from .order_serializers import OrderSerializer
        return OrderSerializer
    
    def list(self, request):
        """List orders with filtering"""
        user_id = request.query_params.get('user_id')
        status = request.query_params.get('status')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        result = mongodb_manager.list_orders(
            user_id=user_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )
        
        return Response({
            'count': result['total'],
            'next': None if len(result['items']) < page_size else f"?page={page + 1}",
            'previous': None if page == 1 else f"?page={page - 1}",
            'results': result['items']
        })
    
    def retrieve(self, request, pk=None):
        """Get single order by ID"""
        order = mongodb_manager.get_order_by_id(str(pk))
        if not order:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(order)


# MongoDB Payment API Views
class PaymentAPIViewSet(viewsets.ViewSet):
    """ViewSet for MongoDB Payments - Read Only"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        from .payment_serializers import PaymentSerializer
        return PaymentSerializer
    
    def list(self, request):
        """List payments with filtering"""
        order_id = request.query_params.get('order_id')
        user_id = request.query_params.get('user_id')
        status = request.query_params.get('status')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        result = mongodb_manager.list_payments(
            order_id=order_id,
            user_id=user_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )
        
        return Response({
            'count': result['total'],
            'next': None if len(result['items']) < page_size else f"?page={page + 1}",
            'previous': None if page == 1 else f"?page={page - 1}",
            'results': result['items']
        })
    
    def retrieve(self, request, pk=None):
        """Get single payment by ID"""
        payment = mongodb_manager.get_payment_by_id(str(pk))
        if not payment:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(payment)


# MongoDB Category API Views
class CategoryAPIViewSet(viewsets.ViewSet):
    """ViewSet for MongoDB Categories - Full CRUD"""
    permission_classes = [IsAuthenticatedOrReadOnly]  # Read public, write requires auth
    
    def get_serializer_class(self):
        return CategorySerializer
    
    def list(self, request):
        """List categories with filtering"""
        parent_id = request.query_params.get('parent_id')
        is_active = request.query_params.get('is_active')
        top_level_only = request.query_params.get('top_level_only', 'false').lower() == 'true'
        
        # Convert string to boolean if provided
        is_active_bool = None
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
        
        categories = mongodb_manager.list_categories(
            parent_id=parent_id if parent_id else None,
            is_active=is_active_bool,
            top_level_only=top_level_only
        )
        
        # Return in paginated format for consistency
        return Response({
            'count': len(categories),
            'next': None,
            'previous': None,
            'results': categories
        })
    
    def create(self, request):
        """Create a new category"""
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response(category, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """Get single category by ID"""
        category = mongodb_manager.get_category_by_id(str(pk))
        if not category:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(category)
    
    def update(self, request, pk=None):
        """Update category (full update)"""
        category = mongodb_manager.get_category_by_id(str(pk))
        if not category:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            updated_category = serializer.save()
            return Response(updated_category)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        """Update category (partial update)"""
        category = mongodb_manager.get_category_by_id(str(pk))
        if not category:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            updated_category = serializer.save()
            return Response(updated_category)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete category"""
        category = mongodb_manager.get_category_by_id(str(pk))
        if not category:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        success = mongodb_manager.delete_category(str(pk))
        if success:
            return Response({'message': 'Category deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Failed to delete category'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def tree(self, request):
        """Get category tree (hierarchical structure)"""
        all_categories = mongodb_manager.list_categories(is_active=True)
        
        # Build tree structure
        category_dict = {cat['id']: {**cat, 'children': []} for cat in all_categories}
        root_categories = []
        
        for cat in all_categories:
            if cat['parent_id']:
                parent = category_dict.get(cat['parent_id'])
                if parent:
                    parent['children'].append(category_dict[cat['id']])
            else:
                root_categories.append(category_dict[cat['id']])
        
        return Response({'results': root_categories})


# MongoDB FAQ API Views
class FAQViewSet(viewsets.ViewSet):
    """ViewSet for FAQ operations using MongoDB"""
    permission_classes = [AllowAny]  # Public endpoint for chatbot
    
    def list(self, request):
        """Get all active FAQs"""
        category = request.query_params.get('category', None)
        faqs = mongodb_manager.list_faqs(category=category, is_active=True)
        return Response({'results': faqs})
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search FAQs by query"""
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'results': []})
        
        faqs = mongodb_manager.search_faqs(query, is_active=True)
        return Response({'results': faqs})
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all FAQ categories"""
        faqs = mongodb_manager.list_faqs(is_active=True)
        categories = list(set([faq.get('category', 'general') for faq in faqs]))
        return Response({'results': sorted(categories)})

