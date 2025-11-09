"""
Internal API client that directly calls API viewsets/serializers
This allows views to consume APIs without HTTP overhead
"""
from typing import Optional, Dict, List
from django.http import QueryDict
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory


class InternalAPIClient:
    """Client that directly calls API viewsets without HTTP overhead"""
    
    def __init__(self, request=None):
        """Initialize with optional Django request object"""
        self.request = request
        self.factory = APIRequestFactory()
    
    def _create_drf_request(self, method='GET', path='', data=None, query_params=None):
        """Create DRF request object"""
        if self.request:
            # Use actual request if available
            drf_request = Request(self.request)
            if query_params:
                # Create QueryDict properly for DRF
                from django.http import QueryDict as DjangoQueryDict
                query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
                drf_request._full_data = {}
                drf_request.query_params = DjangoQueryDict(query_string, mutable=True)
            return drf_request
        else:
            # Create mock request for internal calls
            if method == 'GET':
                request = self.factory.get(path, query_params or {})
            elif method == 'POST':
                request = self.factory.post(path, data or {})
            else:
                request = self.factory.get(path, query_params or {})
            return Request(request)
    
    # Products API methods
    def get_products(self, category: Optional[str] = None, search: Optional[str] = None, 
                     max_price: Optional[str] = None, sort_by: Optional[str] = None,
                     date_from: Optional[str] = None, date_to: Optional[str] = None,
                     page: int = 1, page_size: int = 1000) -> Dict:
        """Get products list by calling ProductAPIViewSet"""
        from .api_views import ProductAPIViewSet
        from rest_framework.request import Request
        
        # Build query parameters - only include non-None and non-empty values
        query_params = {
            'page': str(page),
            'page_size': str(page_size)
        }
        
        # Strip whitespace and only add if not empty
        if category and category.strip():
            query_params['category'] = category.strip()
        if search and search.strip():
            query_params['q'] = search.strip()
        if max_price and max_price.strip():
            query_params['max_price'] = max_price.strip()
        if sort_by and sort_by.strip():
            query_params['sort'] = sort_by.strip()
        if date_from and date_from.strip():
            query_params['date_from'] = date_from.strip()
        if date_to and date_to.strip():
            query_params['date_to'] = date_to.strip()
        
        # Create a mock request with query parameters
        mock_request = self.factory.get('/api/products/', query_params)
        
        drf_request = Request(mock_request)
        viewset = ProductAPIViewSet()
        viewset.action = 'list'
        viewset.request = drf_request
        
        response = viewset.list(drf_request)
        
        # Convert DRF response to dict format
        result = response.data
        return {
            'items': result.get('results', []),
            'total': result.get('count', 0),
            'page': page,
            'page_size': page_size
        }
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get single product by ID"""
        from .api_views import ProductAPIViewSet
        from rest_framework.request import Request
        
        mock_request = self.factory.get(f'/api/products/{product_id}/')
        drf_request = Request(mock_request)
        viewset = ProductAPIViewSet()
        viewset.action = 'retrieve'
        viewset.request = drf_request
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.retrieve(drf_request, pk=product_id)
        
        if response.status_code == 200:
            return response.data
        return None
    
    def get_new_arrivals(self, limit: int = 4) -> List[Dict]:
        """Get new arrivals"""
        from .api_views import ProductAPIViewSet
        from rest_framework.request import Request
        
        mock_request = self.factory.get('/api/products/new_arrivals/')
        drf_request = Request(mock_request)
        viewset = ProductAPIViewSet()
        viewset.action = 'new_arrivals'
        viewset.request = drf_request
        
        response = viewset.new_arrivals(drf_request)
        return response.data.get('results', [])[:limit]
    
    def get_related_products(self, product_id: str) -> List[Dict]:
        """Get related products"""
        from .api_views import ProductAPIViewSet
        from rest_framework.request import Request
        
        mock_request = self.factory.get(f'/api/products/{product_id}/related/')
        drf_request = Request(mock_request)
        viewset = ProductAPIViewSet()
        viewset.action = 'related'
        viewset.request = drf_request
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.related(drf_request, pk=product_id)
        return response.data.get('results', [])
    
    def get_active_sliders(self) -> List[Dict]:
        """Get active sliders"""
        from dashboard.api_views import SliderViewSet
        from rest_framework.request import Request
        
        mock_request = self.factory.get('/api/dashboard/sliders/active/')
        drf_request = Request(mock_request)
        viewset = SliderViewSet()
        viewset.action = 'active'
        viewset.request = drf_request
        
        response = viewset.active(drf_request)
        return response.data if isinstance(response.data, list) else response.data.get('results', [])
    
    def get_categories(self, parent_id: Optional[str] = None, is_active: Optional[bool] = None, 
                      top_level_only: bool = False) -> Dict:
        """Get categories list"""
        from .api_views import CategoryAPIViewSet
        from rest_framework.request import Request
        
        query_params = {}
        if parent_id:
            query_params['parent_id'] = parent_id
        if is_active is not None:
            query_params['is_active'] = str(is_active).lower()
        if top_level_only:
            query_params['top_level_only'] = 'true'
        
        mock_request = self.factory.get('/api/categories/', query_params)
        drf_request = Request(mock_request)
        viewset = CategoryAPIViewSet()
        viewset.action = 'list'
        viewset.request = drf_request
        
        response = viewset.list(drf_request)
        result = response.data
        
        # Handle both list and dict responses
        if isinstance(result, list):
            return {
                'items': result,
                'total': len(result)
            }
        else:
            return {
                'items': result.get('results', []),
                'total': result.get('count', 0)
            }
    
    def get_category(self, category_id: str) -> Optional[Dict]:
        """Get single category by ID"""
        from .api_views import CategoryAPIViewSet
        from rest_framework.request import Request
        
        mock_request = self.factory.get(f'/api/categories/{category_id}/')
        drf_request = Request(mock_request)
        viewset = CategoryAPIViewSet()
        viewset.action = 'retrieve'
        viewset.request = drf_request
        viewset.kwargs = {'pk': category_id}
        
        response = viewset.retrieve(drf_request, pk=category_id)
        if response.status_code == 200:
            return response.data
        return None
    
    def get_category_tree(self) -> List[Dict]:
        """Get category tree (hierarchical)"""
        from .api_views import CategoryAPIViewSet
        from rest_framework.request import Request
        
        mock_request = self.factory.get('/api/categories/tree/')
        drf_request = Request(mock_request)
        viewset = CategoryAPIViewSet()
        viewset.action = 'tree'
        viewset.request = drf_request
        
        response = viewset.tree(drf_request)
        return response.data.get('results', [])
    
    def get_orders(self, user_id: Optional[str] = None, status: Optional[str] = None,
                   date_from: Optional[str] = None, date_to: Optional[str] = None,
                   page: int = 1, page_size: int = 20) -> Dict:
        """Get orders list"""
        from .api_views import OrderAPIViewSet
        from rest_framework.request import Request
        
        query_params = {
            'page': str(page),
            'page_size': str(page_size)
        }
        
        if user_id:
            query_params['user_id'] = user_id
        if status:
            query_params['status'] = status
        if date_from:
            query_params['date_from'] = date_from
        if date_to:
            query_params['date_to'] = date_to
        
        mock_request = self.factory.get('/api/orders/', query_params)
        drf_request = Request(mock_request)
        viewset = OrderAPIViewSet()
        viewset.action = 'list'
        viewset.request = drf_request
        
        response = viewset.list(drf_request)
        result = response.data
        
        return {
            'items': result.get('results', []),
            'total': result.get('count', 0),
            'page': page,
            'page_size': page_size
        }
    
    def get_payments(self, order_id: Optional[str] = None, user_id: Optional[str] = None,
                     status: Optional[str] = None, date_from: Optional[str] = None,
                     date_to: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict:
        """Get payments list"""
        from .api_views import PaymentAPIViewSet
        from rest_framework.request import Request
        
        query_params = {
            'page': str(page),
            'page_size': str(page_size)
        }
        
        if order_id:
            query_params['order_id'] = order_id
        if user_id:
            query_params['user_id'] = user_id
        if status:
            query_params['status'] = status
        if date_from:
            query_params['date_from'] = date_from
        if date_to:
            query_params['date_to'] = date_to
        
        mock_request = self.factory.get('/api/payments/', query_params)
        drf_request = Request(mock_request)
        viewset = PaymentAPIViewSet()
        viewset.action = 'list'
        viewset.request = drf_request
        
        response = viewset.list(drf_request)
        result = response.data
        
        return {
            'items': result.get('results', []),
            'total': result.get('count', 0),
            'page': page,
            'page_size': page_size
        }


# Fallback direct access for when API is unavailable
class DirectAccessClient:
    """Fallback client that directly accesses database/MongoDB"""
    
    def __init__(self):
        from .mongodb_utils import mongodb_manager
        from dashboard.models import Slider
        self.mongodb_manager = mongodb_manager
        self.Slider = Slider
    
    def get_products(self, category=None, search=None, max_price=None, 
                     sort_by=None, date_from=None, date_to=None,
                     page=1, page_size=1000):
        """Direct access to products"""
        return self.mongodb_manager.list_products(
            category=category,
            search=search,
            max_price=max_price,
            sort_by=sort_by,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )
    
    def get_product(self, product_id):
        """Direct access to product"""
        return self.mongodb_manager.get_product_by_id(str(product_id))
    
    def get_new_arrivals(self, limit=4):
        """Direct access to new arrivals"""
        result = self.mongodb_manager.list_products(
            sort_by='newest',
            page=1,
            page_size=limit
        )
        return result['items']
    
    def get_related_products(self, product_id):
        """Direct access to related products"""
        product = self.mongodb_manager.get_product_by_id(str(product_id))
        if not product or not product.get('category_id'):
            return []
        
        # Convert category_id to string if it's an ObjectId
        category_id = product['category_id']
        if not isinstance(category_id, str):
            category_id = str(category_id)
        
        result = self.mongodb_manager.list_products(
            category=category_id,
            page=1,
            page_size=4
        )
        return [p for p in result['items'] if p['id'] != product['id']][:4]
    
    def get_active_sliders(self):
        """Direct access to sliders"""
        sliders = self.Slider.objects.filter(status='active').order_by('order')
        return [{
            'id': slider.id,
            'title': slider.title,
            'subtitle': slider.subtitle,
            'description': slider.description,
            'img': slider.img,
            'link': slider.link,
            'status': slider.status,
            'order': slider.order,
        } for slider in sliders]
    
    def get_categories(self, parent_id=None, is_active=None, top_level_only=False):
        """Direct access to categories"""
        result = self.mongodb_manager.list_categories(
            parent_id=parent_id,
            is_active=is_active,
            top_level_only=top_level_only
        )
        return {
            'items': result,
            'total': len(result)
        }
    
    def get_category(self, category_id):
        """Direct access to category"""
        return self.mongodb_manager.get_category_by_id(str(category_id))
    
    def get_category_tree(self):
        """Direct access to category tree"""
        # Get all categories and build tree structure
        all_categories = self.mongodb_manager.list_categories(is_active=True)
        # Build tree (simplified - in production, use proper tree building)
        return all_categories
    
    def get_orders(self, user_id=None, status=None, date_from=None, date_to=None, page=1, page_size=20):
        """Direct access to orders"""
        return self.mongodb_manager.list_orders(
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )
    
    def get_payments(self, order_id=None, user_id=None, status=None, date_from=None, date_to=None, page=1, page_size=20):
        """Direct access to payments"""
        return self.mongodb_manager.list_payments(
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )


def get_api_client(request=None, use_api=True):
    """Get API client - uses internal API if available, falls back to direct access"""
    if use_api:
        try:
            return InternalAPIClient(request)
        except Exception:
            # Fallback to direct access if API client fails
            return DirectAccessClient()
    return DirectAccessClient()

