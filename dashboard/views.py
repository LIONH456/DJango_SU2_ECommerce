from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import os
import uuid
import logging
from pathlib import Path
from .models import Slider
from django.db import models
from main.api_client import get_api_client

logger = logging.getLogger(__name__)

# Create your views here.
@login_required
def index(request):
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    context = {
        'active_page': 'dashboard'
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def sliders_list(request):
    """Display list of all sliders from MongoDB"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Fetch sliders from MongoDB
    from main.mongodb_utils import mongodb_manager
    try:
        sliders_data = mongodb_manager.list_sliders(status=None)  # Get all sliders
        # Convert to Slider-like objects for template compatibility
        class SliderObject:
            def __init__(self, data):
                self.id = data.get('id')
                self.title = data.get('title', '')
                self.subtitle = data.get('subtitle', '')
                self.description = data.get('description', '')
                self.img = data.get('img', '')
                self.link = data.get('link', '')
                self.status = data.get('status', 'active')
                self.order = data.get('order', 0)
        
        sliders = [SliderObject(s) for s in sliders_data] if sliders_data else []
    except Exception as e:
        messages.error(request, f'Error loading sliders from MongoDB: {str(e)}')
        # Fallback to Django ORM
        sliders = Slider.objects.all()
    
    context = {
        'sliders': sliders,
        'active_page': 'sliders'
    }
    return render(request, 'dashboard/Sliders.html', context)

@login_required
def slider_create(request):
    """Create a new slider"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Fetch sliders from MongoDB
    from main.mongodb_utils import mongodb_manager
    
    if request.method == 'POST':
        try:
            # Get the order number from form
            order = request.POST.get('order', 0)
            if order:
                order = int(order)
            else:
                # Auto-assign order number (next available)
                order = mongodb_manager.get_next_slider_order()
            
            # Create slider data
            slider_data = {
                'title': request.POST.get('title', ''),
                'subtitle': request.POST.get('subtitle', ''),
                'description': request.POST.get('description', ''),
                'img': request.POST.get('img', ''),
                'link': request.POST.get('link', ''),
                'status': request.POST.get('status', 'active'),
                'order': order
            }
            
            # Create slider in MongoDB
            slider_id = mongodb_manager.create_slider(slider_data)
            
            if slider_id:
                messages.success(request, 'Slider created successfully!')
                return redirect('dashboard:sliders_list')
            else:
                messages.error(request, 'Error creating slider in MongoDB')
        except Exception as e:
            messages.error(request, f'Error creating slider: {str(e)}')
    
    # Get next available order number for the form
    next_order = mongodb_manager.get_next_slider_order()
    
    context = {
        'slider': None,
        'active_page': 'sliders',
        'next_order': next_order
    }
    return render(request, 'dashboard/slider_form.html', context)

@login_required
def slider_edit(request, slider_id):
    """Edit an existing slider"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Fetch slider from MongoDB
    from main.mongodb_utils import mongodb_manager
    slider = mongodb_manager.get_slider_by_id(slider_id)
    
    if not slider:
        messages.error(request, 'Slider not found')
        return redirect('dashboard:sliders_list')
    
    if request.method == 'POST':
        try:
            old_order = slider.get('order', 0)
            new_order = request.POST.get('order', 0)
            if new_order:
                new_order = int(new_order)
            else:
                new_order = old_order
            
            # Update slider data
            update_data = {
                'title': request.POST.get('title', ''),
                'subtitle': request.POST.get('subtitle', ''),
                'description': request.POST.get('description', ''),
                'img': request.POST.get('img', ''),
                'link': request.POST.get('link', ''),
                'status': request.POST.get('status', 'active'),
                'order': new_order
            }
            
            # Update slider in MongoDB
            success = mongodb_manager.update_slider(slider_id, update_data)
            
            if success:
                messages.success(request, 'Slider updated successfully!')
                return redirect('dashboard:sliders_list')
            else:
                messages.error(request, 'Error updating slider in MongoDB')
        except Exception as e:
            messages.error(request, f'Error updating slider: {str(e)}')
    
    context = {
        'slider': slider,
        'active_page': 'sliders'
    }
    return render(request, 'dashboard/slider_form.html', context)

@login_required
def slider_delete(request, slider_id):
    """Delete a slider"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Delete slider from MongoDB
    from main.mongodb_utils import mongodb_manager
    try:
        success = mongodb_manager.delete_slider(slider_id)
        
        if success:
            messages.success(request, 'Slider deleted successfully!')
        else:
            messages.error(request, 'Error deleting slider from MongoDB')
    except Exception as e:
        messages.error(request, f'Error deleting slider: {str(e)}')
    
    return redirect('dashboard:sliders_list')

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def slider_toggle_status(request, slider_id):
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Access denied. Superuser privileges required.'}, status=403)
    """Toggle slider status via AJAX"""
    try:
        from main.mongodb_utils import mongodb_manager
        new_status = mongodb_manager.toggle_slider_status(slider_id)
        
        if new_status:
            return JsonResponse({
                'success': True,
                            'status': new_status
        })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Slider not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def slider_reorder(request):
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Access denied. Superuser privileges required.'}, status=403)
    """Reorder sliders via AJAX"""
    try:
        from main.mongodb_utils import mongodb_manager
        data = json.loads(request.body)
        items = data.get('items', [])
        
        # Reorder sliders in MongoDB
        success = mongodb_manager.reorder_sliders(items)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error reordering sliders'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# Product Management Views
@login_required
def products_list(request):
    """Display list of all products with search, filters, and pagination"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    api_client = get_api_client(request, use_api=True)
    
    # Get filter parameters
    search_query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Get page number
    page = request.GET.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    # Pagination settings
    per_page = 10
    
    # Get categories for filter dropdown
    try:
        categories_result = api_client.get_categories(is_active=True)
        all_categories = categories_result.get('items', [])
    except:
        all_categories = []
    
    try:
        # Build query parameters
        params = {
            'page': page,
            'page_size': per_page,
        }
        
        # Only add search if it's not empty
        if search_query:
            params['search'] = search_query
        # Apply filters even if search is empty
        if category_filter:
            params['category'] = category_filter
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        
        result = api_client.get_products(**params)
        products = result.get('items', [])
        total = result.get('total', 0)
    except Exception as e:
        products = []
        total = 0
        messages.error(request, f'Error loading products: {str(e)}')
    
    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages
    
    context = {
        'products': products,
        'active_page': 'products',
        'search_query': search_query,
        'category_filter': category_filter,
        'date_from': date_from,
        'date_to': date_to,
        'categories': all_categories,
        'current_page': page,
        'total_pages': total_pages,
        'total': total,
        'has_prev': has_prev,
        'has_next': has_next,
        'per_page': per_page,
    }
    return render(request, 'dashboard/products_list.html', context)

def handle_product_images(request, existing_images=None):
    """Handle product image uploads, URLs, and removal"""
    images_path = []
    
    # Start with existing images
    if existing_images:
        images_path.extend(existing_images)
    
    # Handle uploaded files
    if 'images' in request.FILES:
        uploaded_files = request.FILES.getlist('images')
        static_dir = Path(settings.BASE_DIR) / 'static' / 'images' / 'products'
        static_dir.mkdir(parents=True, exist_ok=True)
        
        for uploaded_file in uploaded_files:
            # Generate unique filename
            file_extension = uploaded_file.name.split('.')[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = static_dir / unique_filename
            
            # Save file
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Store relative path for static files
            relative_path = f"images/products/{unique_filename}"
            images_path.append(relative_path)
    
    # Handle URL input (if provided in images_urls field)
    # Note: URLs will be added in the order they appear in the image_order field during form processing
    if 'images_urls' in request.POST:
        urls_str = request.POST.get('images_urls', '').strip()
        if urls_str:
            urls = [url.strip() for url in urls_str.split(',') if url.strip()]
            images_path.extend(urls)
    
    # Handle removed images
    if 'removed_images' in request.POST and request.POST['removed_images']:
        removed = [r.strip() for r in request.POST['removed_images'].split(',') if r.strip()]
        images_path = [img for img in images_path if img not in removed]
        
        # Delete removed image files (only for local files, not URLs)
        for img_path in removed:
            if not img_path.startswith('http://') and not img_path.startswith('https://'):
                full_path = Path(settings.BASE_DIR) / 'static' / img_path.strip()
                if full_path.exists():
                    try:
                        os.remove(full_path)
                    except Exception:
                        pass
    
    return images_path

@login_required
def product_create(request):
    """Create a new product"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    api_client = get_api_client(request, use_api=True)
    
    # Get categories for dropdown
    try:
        categories_result = api_client.get_categories(is_active=True)
        categories = categories_result.get('items', [])
    except Exception:
        categories = []
    
    if request.method == 'POST':
        try:
            from main.api_views import ProductAPIViewSet
            from rest_framework.request import Request as DRFRequest
            import json
            
            # Handle image uploads
            uploaded_images = handle_product_images(request)
            
            # Handle image reordering if provided
            if 'image_order' in request.POST and request.POST['image_order']:
                order_str = request.POST['image_order'].strip()
                if order_str:
                    ordered_paths = [p.strip() for p in order_str.split(',') if p.strip()]
                    # Filter uploaded_images to match the order
                    ordered_images = []
                    for path in ordered_paths:
                        if path in uploaded_images:
                            ordered_images.append(path)
                    # Add any remaining images not in order
                    for img in uploaded_images:
                        if img not in ordered_images:
                            ordered_images.append(img)
                    uploaded_images = ordered_images
            
            # Convert form data to proper format
            data = dict(request.POST)
            
            # Add uploaded images (ensure it's always a list)
            data['images'] = uploaded_images if isinstance(uploaded_images, list) else [uploaded_images] if uploaded_images else []
            
            # Handle tags (comma-separated)
            if 'tags' in data and data['tags']:
                tags_str = data['tags'][0].strip() if isinstance(data['tags'], list) else str(data['tags']).strip()
                if tags_str:
                    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                    data['tags'] = tags
                else:
                    data['tags'] = []
            
            # Convert boolean fields
            if 'is_available' in data:
                is_available_val = data['is_available'][0] if isinstance(data['is_available'], list) else data['is_available']
                data['is_available'] = str(is_available_val).lower() == 'true'
            
            # Convert numeric fields
            for field in ['price', 'compare_price', 'quantity']:
                if field in data:
                    field_val = data[field][0] if isinstance(data[field], list) else data[field]
                    try:
                        data[field] = float(field_val) if field in ['price', 'compare_price'] else int(field_val)
                    except (ValueError, TypeError):
                        if field == 'quantity':
                            data[field] = 0
                        else:
                            data[field] = None
            
            # Handle empty strings - convert lists to single values (except images and tags which must stay as lists)
            for key in list(data.keys()):
                # Skip images and tags - they must remain as lists
                if key in ['images', 'tags']:
                    continue
                if isinstance(data[key], list) and len(data[key]) == 1:
                    data[key] = data[key][0] if data[key][0] else None
                elif isinstance(data[key], list) and len(data[key]) == 0:
                    data[key] = None
            
            # Ensure images is always a list (double-check after list conversion)
            if 'images' in data:
                if not isinstance(data['images'], list):
                    data['images'] = [data['images']] if data['images'] else []
            
            # Ensure tags is always a list (double-check after list conversion)
            if 'tags' in data:
                if not isinstance(data['tags'], list):
                    data['tags'] = [data['tags']] if data['tags'] else []
            
            # Wrap Django request in DRF Request object
            drf_request = DRFRequest(request)
            
            # Override request.data with our processed data
            # DRF Request has a _full_data attribute that controls request.data property
            # Make a copy to avoid mutating the original
            import copy
            data_copy = copy.deepcopy(data)
            drf_request._full_data = data_copy
            drf_request._data = data_copy
            
            viewset = ProductAPIViewSet()
            viewset.action = 'create'
            viewset.request = drf_request
            viewset.format_kwarg = None
            
            response = viewset.create(drf_request)
            
            if response.status_code == 201:
                messages.success(request, '✅ Product created successfully!')
                return redirect('dashboard:products_list')
            else:
                error_data = response.data if hasattr(response, 'data') else {}
                if isinstance(error_data, dict):
                    error_msgs = []
                    for field, errors in error_data.items():
                        if isinstance(errors, list):
                            error_msgs.append(f"{field}: {', '.join(errors)}")
                        else:
                            error_msgs.append(f"{field}: {errors}")
                    error_msg = '; '.join(error_msgs) if error_msgs else str(error_data)
                else:
                    error_msg = str(error_data)
                messages.error(request, f'❌ Error creating product: {error_msg}')
                
                # Preserve form data on error - create product dict from POST data
                form_product = {
                    'name': request.POST.get('name', ''),
                    'slug': request.POST.get('slug', ''),
                    'description': request.POST.get('description', ''),
                    'price': request.POST.get('price', ''),
                    'compare_price': request.POST.get('compare_price', ''),
                    'sku': request.POST.get('sku', ''),
                    'quantity': request.POST.get('quantity', 0),
                    'category_id': request.POST.get('category_id', ''),
                    'is_available': request.POST.get('is_available', 'true').lower() == 'true',
                    'tags': [tag.strip() for tag in request.POST.get('tags', '').split(',') if tag.strip()],
                    'images': uploaded_images,
                }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            messages.error(request, f'❌ Error creating product: {str(e)}')
            # Log full error for debugging
            print(f"Product create error: {error_trace}")
            
            # Preserve form data on exception
            form_product = {
                'name': request.POST.get('name', ''),
                'slug': request.POST.get('slug', ''),
                'description': request.POST.get('description', ''),
                'price': request.POST.get('price', ''),
                'compare_price': request.POST.get('compare_price', ''),
                'sku': request.POST.get('sku', ''),
                'quantity': request.POST.get('quantity', 0),
                'category_id': request.POST.get('category_id', ''),
                'is_available': request.POST.get('is_available', 'true').lower() == 'true',
                'tags': [tag.strip() for tag in request.POST.get('tags', '').split(',') if tag.strip()],
                'images': uploaded_images if 'uploaded_images' in locals() else [],
            }
    
    # Use form_product if it exists (on error), otherwise None
    product = form_product if 'form_product' in locals() else None
    
    context = {
        'product': product,
        'categories': categories,
        'active_page': 'products'
    }
    return render(request, 'dashboard/product_form.html', context)

@login_required
def product_edit(request, product_id):
    """Edit an existing product"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    api_client = get_api_client(request, use_api=True)
    
    # Get product
    try:
        product = api_client.get_product(str(product_id))
        if not product:
            messages.error(request, 'Product not found')
            return redirect('dashboard:products_list')
    except Exception as e:
        messages.error(request, f'Error loading product: {str(e)}')
        return redirect('dashboard:products_list')
    
    # Get categories for dropdown
    try:
        categories_result = api_client.get_categories(is_active=True)
        categories = categories_result.get('items', [])
    except Exception:
        categories = []
    
    if request.method == 'POST':
        try:
            from main.api_views import ProductAPIViewSet
            from rest_framework.request import Request as DRFRequest
            import json
            
            # Handle image uploads - merge with existing images
            existing_images = product.get('images', [])
            uploaded_images = handle_product_images(request, existing_images)
            
            # Handle image reordering if provided
            if 'image_order' in request.POST and request.POST['image_order']:
                order_str = request.POST['image_order'].strip()
                if order_str:
                    ordered_paths = [p.strip() for p in order_str.split(',') if p.strip()]
                    # Filter uploaded_images to match the order
                    ordered_images = []
                    for path in ordered_paths:
                        if path in uploaded_images:
                            ordered_images.append(path)
                    # Add any remaining images not in order
                    for img in uploaded_images:
                        if img not in ordered_images:
                            ordered_images.append(img)
                    uploaded_images = ordered_images
            
            # Convert form data to proper format
            data = dict(request.POST)
            
            # Add uploaded images (ensure it's always a list)
            data['images'] = uploaded_images if isinstance(uploaded_images, list) else [uploaded_images] if uploaded_images else []
            
            # Handle tags (comma-separated)
            if 'tags' in data and data['tags']:
                tags_str = data['tags'][0].strip() if isinstance(data['tags'], list) else str(data['tags']).strip()
                if tags_str:
                    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                    data['tags'] = tags
                else:
                    data['tags'] = []
            elif 'tags' not in data:
                data['tags'] = []
            
            # Convert boolean fields
            if 'is_available' in data:
                is_available_val = data['is_available'][0] if isinstance(data['is_available'], list) else data['is_available']
                data['is_available'] = str(is_available_val).lower() == 'true'
            
            # Convert numeric fields
            for field in ['price', 'compare_price', 'quantity']:
                if field in data:
                    field_val = data[field][0] if isinstance(data[field], list) else data[field]
                    try:
                        data[field] = float(field_val) if field in ['price', 'compare_price'] else int(field_val)
                    except (ValueError, TypeError):
                        if field == 'quantity':
                            data[field] = 0
                        else:
                            data[field] = None
            
            # Handle empty strings - convert lists to single values (except images and tags which must stay as lists)
            for key in list(data.keys()):
                # Skip images and tags - they must remain as lists
                if key in ['images', 'tags']:
                    continue
                if isinstance(data[key], list) and len(data[key]) == 1:
                    data[key] = data[key][0] if data[key][0] else None
                elif isinstance(data[key], list) and len(data[key]) == 0:
                    data[key] = None
            
            # Ensure images is always a list
            if 'images' in data:
                if not isinstance(data['images'], list):
                    data['images'] = [data['images']] if data['images'] else []
            
            # Ensure tags is always a list
            if 'tags' in data:
                if not isinstance(data['tags'], list):
                    data['tags'] = [data['tags']] if data['tags'] else []
            
            # Wrap Django request in DRF Request object
            drf_request = DRFRequest(request)
            
            # Override request.data with our processed data
            # Make a copy to avoid mutating the original
            import copy
            data_copy = copy.deepcopy(data)
            drf_request._full_data = data_copy
            drf_request._data = data_copy
            
            viewset = ProductAPIViewSet()
            viewset.action = 'partial_update'
            viewset.request = drf_request
            viewset.kwargs = {'pk': str(product_id)}
            viewset.format_kwarg = None
            
            response = viewset.partial_update(drf_request, pk=str(product_id))
            
            if response.status_code == 200:
                messages.success(request, '✅ Product updated successfully!')
                return redirect('dashboard:products_list')
            else:
                error_data = response.data if hasattr(response, 'data') else {}
                if isinstance(error_data, dict):
                    error_msgs = []
                    for field, errors in error_data.items():
                        if isinstance(errors, list):
                            error_msgs.append(f"{field}: {', '.join(errors)}")
                        else:
                            error_msgs.append(f"{field}: {errors}")
                    error_msg = '; '.join(error_msgs) if error_msgs else str(error_data)
                else:
                    error_msg = str(error_data)
                messages.error(request, f'❌ Error updating product: {error_msg}')
                
                # Preserve form data on error - merge POST data with existing product
                form_product = product.copy() if product else {}
                form_product.update({
                    'name': request.POST.get('name', form_product.get('name', '')),
                    'slug': request.POST.get('slug', form_product.get('slug', '')),
                    'description': request.POST.get('description', form_product.get('description', '')),
                    'price': request.POST.get('price', form_product.get('price', '')),
                    'compare_price': request.POST.get('compare_price', form_product.get('compare_price', '')),
                    'sku': request.POST.get('sku', form_product.get('sku', '')),
                    'quantity': request.POST.get('quantity', form_product.get('quantity', 0)),
                    'category_id': request.POST.get('category_id', form_product.get('category_id', '')),
                    'is_available': request.POST.get('is_available', 'true').lower() == 'true',
                    'tags': [tag.strip() for tag in request.POST.get('tags', '').split(',') if tag.strip()],
                    'images': uploaded_images,
                })
                product = form_product
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            messages.error(request, f'❌ Error updating product: {str(e)}')
            print(f"Product update error: {error_trace}")
            
            # Preserve form data on exception
            form_product = product.copy() if product else {}
            form_product.update({
                'name': request.POST.get('name', form_product.get('name', '')),
                'slug': request.POST.get('slug', form_product.get('slug', '')),
                'description': request.POST.get('description', form_product.get('description', '')),
                'price': request.POST.get('price', form_product.get('price', '')),
                'compare_price': request.POST.get('compare_price', form_product.get('compare_price', '')),
                'sku': request.POST.get('sku', form_product.get('sku', '')),
                'quantity': request.POST.get('quantity', form_product.get('quantity', 0)),
                'category_id': request.POST.get('category_id', form_product.get('category_id', '')),
                'is_available': request.POST.get('is_available', 'true').lower() == 'true',
                'tags': [tag.strip() for tag in request.POST.get('tags', '').split(',') if tag.strip()],
                'images': uploaded_images if 'uploaded_images' in locals() else form_product.get('images', []),
            })
            product = form_product
    
    context = {
        'product': product,
        'categories': categories,
        'active_page': 'products'
    }
    return render(request, 'dashboard/product_form.html', context)

@login_required
def product_delete(request, product_id):
    """Delete a product"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    try:
        from main.api_views import ProductAPIViewSet
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        api_request = factory.delete(f'/api/products/{product_id}/')
        drf_request = Request(api_request)
        drf_request.user = request.user
        
        viewset = ProductAPIViewSet()
        viewset.action = 'destroy'
        viewset.request = drf_request
        viewset.kwargs = {'pk': str(product_id)}
        
        response = viewset.destroy(drf_request, pk=str(product_id))
        
        if response.status_code == 204:
            messages.success(request, 'Product deleted successfully!')
        else:
            error_msg = response.data if hasattr(response, 'data') else str(response)
            messages.error(request, f'Error deleting product: {error_msg}')
    except Exception as e:
        messages.error(request, f'Error deleting product: {str(e)}')
    
    return redirect('dashboard:products_list')

# Category Management Views
@login_required
def categories_list(request):
    """Display list of all categories with search and pagination"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    api_client = get_api_client(request, use_api=True)
    
    # Get search query
    search_query = request.GET.get('q', '').strip()
    
    # Get page number
    page = request.GET.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    # Pagination settings
    per_page = 10
    
    try:
        # Get all categories (for now, we'll filter and paginate manually since API might not support it)
        result = api_client.get_categories()
        all_categories = result.get('items', [])
        
        # Apply search filter
        if search_query:
            search_lower = search_query.lower()
            all_categories = [
                cat for cat in all_categories
                if search_lower in cat.get('name', '').lower() or 
                   search_lower in cat.get('slug', '').lower() or
                   search_lower in (cat.get('description', '') or '').lower()
            ]
        
        # Build hierarchical structure for display
        category_map = {}
        top_level_categories = []
        
        # First pass: create map and identify top-level categories
        for cat in all_categories:
            category_map[cat['id']] = cat
            cat['children'] = []
            cat['level'] = 0
        
        # Second pass: build tree and calculate levels
        for cat in all_categories:
            parent_id = cat.get('parent_id')
            if parent_id and parent_id in category_map:
                # This is a child category
                category_map[parent_id]['children'].append(cat)
                # Calculate level based on parent
                parent = category_map[parent_id]
                cat['level'] = parent.get('level', 0) + 1
            else:
                # This is a top-level category
                top_level_categories.append(cat)
        
        # Flatten tree for display (maintaining hierarchy order)
        def flatten_categories(cats, result_list):
            for cat in sorted(cats, key=lambda x: x.get('sort_order', 0)):
                result_list.append(cat)
                if cat['children']:
                    flatten_categories(cat['children'], result_list)
        
        categories_flat = []
        flatten_categories(top_level_categories, categories_flat)
        
        total = len(categories_flat)
        
        # Manual pagination
        start = (page - 1) * per_page
        end = start + per_page
        categories = categories_flat[start:end]
        
    except Exception as e:
        categories = []
        total = 0
        messages.error(request, f'Error loading categories: {str(e)}')
    
    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages
    
    context = {
        'categories': categories,
        'active_page': 'categories',
        'search_query': search_query,
        'current_page': page,
        'total_pages': total_pages,
        'total': total,
        'has_prev': has_prev,
        'has_next': has_next,
        'per_page': per_page,
    }
    return render(request, 'dashboard/categories_list.html', context)

def handle_category_image(request, existing_image=None):
    """Handle category image upload or URL - saves to both static and staticfiles for VPS compatibility"""
    image_path = existing_image
    
    # Handle uploaded file (priority)
    if 'image' in request.FILES:
        uploaded_file = request.FILES['image']
        
        # Generate unique filename
        file_extension = uploaded_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        relative_path = f"images/categories/{unique_filename}"
        
        # Save to static directory (for development)
        static_dir = Path(settings.BASE_DIR) / 'static' / 'images' / 'categories'
        static_dir.mkdir(parents=True, exist_ok=True)
        static_file_path = static_dir / unique_filename
        
        # Save to staticfiles directory (for production/VPS)
        staticfiles_dir = Path(settings.BASE_DIR) / 'staticfiles' / 'images' / 'categories'
        staticfiles_dir.mkdir(parents=True, exist_ok=True)
        staticfiles_file_path = staticfiles_dir / unique_filename
        
        # Delete old image if exists (only local files)
        if existing_image and not existing_image.startswith('http://') and not existing_image.startswith('https://'):
            # Try to delete from static
            old_static_path = Path(settings.BASE_DIR) / 'static' / existing_image
            if old_static_path.exists():
                try:
                    os.remove(old_static_path)
                except Exception:
                    pass
            # Try to delete from staticfiles
            old_staticfiles_path = Path(settings.BASE_DIR) / 'staticfiles' / existing_image
            if old_staticfiles_path.exists():
                try:
                    os.remove(old_staticfiles_path)
                except Exception:
                    pass
        
        # Read file content once
        file_content = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer for next read
        
        # Save to static directory
        try:
            with open(static_file_path, 'wb+') as destination:
                destination.write(file_content)
        except Exception as e:
            logger.error(f"Error saving to static directory: {e}")
        
        # Save to staticfiles directory (for production)
        try:
            with open(staticfiles_file_path, 'wb+') as destination:
                destination.write(file_content)
        except Exception as e:
            logger.error(f"Error saving to staticfiles directory: {e}")
        
        # Store relative path for static files
        image_path = relative_path
    # Handle URL input (if no file uploaded)
    elif 'image_url' in request.POST and request.POST.get('image_url', '').strip():
        image_path = request.POST.get('image_url', '').strip()
    
    return image_path

@login_required
def category_create(request):
    """Create a new category"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    api_client = get_api_client(request, use_api=True)
    
    # Get parent categories for dropdown
    try:
        parents_result = api_client.get_categories(top_level_only=True, is_active=True)
        parent_categories = parents_result.get('items', [])
    except Exception:
        parent_categories = []
    
    if request.method == 'POST':
        try:
            from main.api_views import CategoryAPIViewSet
            from rest_framework.request import Request
            
            # Handle image upload
            image_path = handle_category_image(request)
            
            # Convert form data to proper format
            data = dict(request.POST)
            
            # Add image path
            if image_path:
                data['image'] = image_path
            
            # Convert boolean fields
            if 'is_active' in data:
                is_active_val = data['is_active'][0] if isinstance(data['is_active'], list) else data['is_active']
                data['is_active'] = str(is_active_val).lower() == 'true'
            
            # Convert numeric fields
            if 'sort_order' in data:
                sort_order_val = data['sort_order'][0] if isinstance(data['sort_order'], list) else data['sort_order']
                try:
                    data['sort_order'] = int(sort_order_val) if sort_order_val else 0
                except (ValueError, TypeError):
                    data['sort_order'] = 0
            
            # Handle empty parent_id
            if 'parent_id' in data:
                parent_val = data['parent_id'][0] if isinstance(data['parent_id'], list) else data['parent_id']
                if not parent_val or (isinstance(parent_val, str) and parent_val.strip() == ''):
                    data['parent_id'] = None
                else:
                    data['parent_id'] = parent_val
            else:
                data['parent_id'] = None
            
            # Handle empty strings - convert lists to single values
            for key in list(data.keys()):
                if isinstance(data[key], list) and len(data[key]) == 1:
                    value = data[key][0]
                    data[key] = value if value else None
                elif isinstance(data[key], list) and len(data[key]) == 0:
                    data[key] = None
            
            # Wrap Django request in DRF Request object
            from rest_framework.request import Request as DRFRequest
            drf_request = DRFRequest(request)
            
            # Override request.data with our processed data
            drf_request._full_data = data
            drf_request._data = data
            
            viewset = CategoryAPIViewSet()
            viewset.action = 'create'
            viewset.request = drf_request
            viewset.format_kwarg = None
            
            response = viewset.create(drf_request)
            
            if response.status_code == 201:
                messages.success(request, '✅ Category created successfully!')
                return redirect('dashboard:categories_list')
            else:
                error_data = response.data if hasattr(response, 'data') else {}
                if isinstance(error_data, dict):
                    error_msgs = []
                    for field, errors in error_data.items():
                        if isinstance(errors, list):
                            error_msgs.append(f"{field}: {', '.join(errors)}")
                        else:
                            error_msgs.append(f"{field}: {errors}")
                    error_msg = '; '.join(error_msgs) if error_msgs else str(error_data)
                else:
                    error_msg = str(error_data)
                messages.error(request, f'❌ Error creating category: {error_msg}')
                
                # Preserve form data on error
                form_category = {
                    'name': request.POST.get('name', ''),
                    'slug': request.POST.get('slug', ''),
                    'description': request.POST.get('description', ''),
                    'image': image_path if image_path else request.POST.get('image_url', ''),
                    'parent_id': request.POST.get('parent_id', ''),
                    'is_active': request.POST.get('is_active', 'true').lower() == 'true',
                    'sort_order': request.POST.get('sort_order', 0),
                }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            messages.error(request, f'❌ Error creating category: {str(e)}')
            print(f"Category create error: {error_trace}")
            
            # Preserve form data on exception
            form_category = {
                'name': request.POST.get('name', ''),
                'slug': request.POST.get('slug', ''),
                'description': request.POST.get('description', ''),
                'image': image_path if 'image_path' in locals() else request.POST.get('image_url', ''),
                'parent_id': request.POST.get('parent_id', ''),
                'is_active': request.POST.get('is_active', 'true').lower() == 'true',
                'sort_order': request.POST.get('sort_order', 0),
            }
    
    # Use form_category if it exists (on error), otherwise None
    category = form_category if 'form_category' in locals() else None
    
    context = {
        'category': category,
        'parent_categories': parent_categories,
        'active_page': 'categories'
    }
    return render(request, 'dashboard/category_form.html', context)

@login_required
def category_edit(request, category_id):
    """Edit an existing category"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    api_client = get_api_client(request, use_api=True)
    
    # Get category
    try:
        category = api_client.get_category(str(category_id))
        if not category:
            messages.error(request, 'Category not found')
            return redirect('dashboard:categories_list')
    except Exception as e:
        messages.error(request, f'Error loading category: {str(e)}')
        return redirect('dashboard:categories_list')
    
    # Get parent categories for dropdown
    try:
        parents_result = api_client.get_categories(top_level_only=True, is_active=True)
        parent_categories = parents_result.get('items', [])
        # Exclude current category from parents (can't be its own parent)
        parent_categories = [p for p in parent_categories if p.get('id') != category_id]
    except Exception:
        parent_categories = []
    
    if request.method == 'POST':
        try:
            from main.api_views import CategoryAPIViewSet
            from rest_framework.request import Request as DRFRequest
            
            # Handle image upload - use existing if no new upload
            existing_image = category.get('image')
            image_path = handle_category_image(request, existing_image)
            
            # Convert form data to proper format
            data = dict(request.POST)
            
            # Add image path (only if changed)
            if image_path:
                data['image'] = image_path
            
            # Convert boolean fields
            if 'is_active' in data:
                is_active_val = data['is_active'][0] if isinstance(data['is_active'], list) else data['is_active']
                data['is_active'] = str(is_active_val).lower() == 'true'
            
            # Convert numeric fields
            if 'sort_order' in data:
                sort_order_val = data['sort_order'][0] if isinstance(data['sort_order'], list) else data['sort_order']
                try:
                    data['sort_order'] = int(sort_order_val) if sort_order_val else 0
                except (ValueError, TypeError):
                    data['sort_order'] = 0
            
            # Handle empty parent_id
            if 'parent_id' in data:
                parent_val = data['parent_id'][0] if isinstance(data['parent_id'], list) else data['parent_id']
                if not parent_val or (isinstance(parent_val, str) and parent_val.strip() == ''):
                    data['parent_id'] = None
                else:
                    data['parent_id'] = parent_val
            else:
                data['parent_id'] = None
            
            # Handle empty strings - convert lists to single values
            for key in list(data.keys()):
                if isinstance(data[key], list) and len(data[key]) == 1:
                    value = data[key][0]
                    data[key] = value if value else None
                elif isinstance(data[key], list) and len(data[key]) == 0:
                    data[key] = None
            
            # Wrap Django request in DRF Request object
            from rest_framework.request import Request as DRFRequest
            drf_request = DRFRequest(request)
            
            # Override request.data with our processed data
            drf_request._full_data = data
            drf_request._data = data
            
            viewset = CategoryAPIViewSet()
            viewset.action = 'partial_update'
            viewset.request = drf_request
            viewset.kwargs = {'pk': str(category_id)}
            viewset.format_kwarg = None
            
            response = viewset.partial_update(drf_request, pk=str(category_id))
            
            if response.status_code == 200:
                messages.success(request, '✅ Category updated successfully!')
                return redirect('dashboard:categories_list')
            else:
                error_data = response.data if hasattr(response, 'data') else {}
                if isinstance(error_data, dict):
                    error_msgs = []
                    for field, errors in error_data.items():
                        if isinstance(errors, list):
                            error_msgs.append(f"{field}: {', '.join(errors)}")
                        else:
                            error_msgs.append(f"{field}: {errors}")
                    error_msg = '; '.join(error_msgs) if error_msgs else str(error_data)
                else:
                    error_msg = str(error_data)
                messages.error(request, f'❌ Error updating category: {error_msg}')
                
                # Preserve form data on error
                form_category = category.copy() if category else {}
                form_category.update({
                    'name': request.POST.get('name', form_category.get('name', '')),
                    'slug': request.POST.get('slug', form_category.get('slug', '')),
                    'description': request.POST.get('description', form_category.get('description', '')),
                    'image': image_path if image_path else request.POST.get('image_url', form_category.get('image', '')),
                    'parent_id': request.POST.get('parent_id', form_category.get('parent_id', '')),
                    'is_active': request.POST.get('is_active', 'true').lower() == 'true',
                    'sort_order': request.POST.get('sort_order', form_category.get('sort_order', 0)),
                })
                category = form_category
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            messages.error(request, f'❌ Error updating category: {str(e)}')
            print(f"Category update error: {error_trace}")
            
            # Preserve form data on exception
            form_category = category.copy() if category else {}
            form_category.update({
                'name': request.POST.get('name', form_category.get('name', '')),
                'slug': request.POST.get('slug', form_category.get('slug', '')),
                'description': request.POST.get('description', form_category.get('description', '')),
                'image': image_path if 'image_path' in locals() else request.POST.get('image_url', form_category.get('image', '')),
                'parent_id': request.POST.get('parent_id', form_category.get('parent_id', '')),
                'is_active': request.POST.get('is_active', 'true').lower() == 'true',
                'sort_order': request.POST.get('sort_order', form_category.get('sort_order', 0)),
            })
            category = form_category
    
    context = {
        'category': category,
        'parent_categories': parent_categories,
        'active_page': 'categories'
    }
    return render(request, 'dashboard/category_form.html', context)

@login_required
def category_delete(request, category_id):
    """Delete a category"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    try:
        from main.api_views import CategoryAPIViewSet
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        api_request = factory.delete(f'/api/categories/{category_id}/')
        drf_request = Request(api_request)
        drf_request.user = request.user
        
        viewset = CategoryAPIViewSet()
        viewset.action = 'destroy'
        viewset.request = drf_request
        viewset.kwargs = {'pk': str(category_id)}
        
        response = viewset.destroy(drf_request, pk=str(category_id))
        
        if response.status_code == 204:
            messages.success(request, 'Category deleted successfully!')
        else:
            error_msg = response.data if hasattr(response, 'data') else str(response)
            messages.error(request, f'Error deleting category: {error_msg}')
    except Exception as e:
        messages.error(request, f'Error deleting category: {str(e)}')
    
    return redirect('dashboard:categories_list')

# Order Management Views
@login_required
def orders_list(request):
    """Display list of all orders with search, filters, and pagination"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    api_client = get_api_client(request, use_api=True)
    
    # Get filter parameters
    status_filter = request.GET.get('status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Get page number
    page = request.GET.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    # Pagination settings
    per_page = 10
    
    try:
        # Build query parameters
        params = {
            'page': page,
            'page_size': per_page,
        }
        
        if status_filter:
            params['status'] = status_filter
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        
        result = api_client.get_orders(**params)
        orders = result.get('items', [])
        total = result.get('total', 0)
    except Exception as e:
        orders = []
        total = 0
        messages.error(request, f'Error loading orders: {str(e)}')
    
    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages
    
    # Order status options
    status_options = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    context = {
        'orders': orders,
        'active_page': 'orders',
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_options': status_options,
        'current_page': page,
        'total_pages': total_pages,
        'total': total,
        'has_prev': has_prev,
        'has_next': has_next,
        'per_page': per_page,
    }
    return render(request, 'dashboard/orders_list.html', context)

# Payment Management Views
@login_required
def payments_list(request):
    """Display list of all payments with search, filters, and pagination"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    api_client = get_api_client(request, use_api=True)
    
    # Get filter parameters
    status_filter = request.GET.get('status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Get page number
    page = request.GET.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    # Pagination settings
    per_page = 10
    
    try:
        # Build query parameters
        params = {
            'page': page,
            'page_size': per_page,
        }
        
        if status_filter:
            params['status'] = status_filter
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        
        result = api_client.get_payments(**params)
        payments = result.get('items', [])
        total = result.get('total', 0)
    except Exception as e:
        payments = []
        total = 0
        messages.error(request, f'Error loading payments: {str(e)}')
    
    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages
    
    # Payment status options
    status_options = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    context = {
        'payments': payments,
        'active_page': 'payments',
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_options': status_options,
        'current_page': page,
        'total_pages': total_pages,
        'total': total,
        'has_prev': has_prev,
        'has_next': has_next,
        'per_page': per_page,
    }
    return render(request, 'dashboard/payments_list.html', context)

# User Management Views
@login_required
def users_list(request):
    """Display list of all users with search, filters, and pagination"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    from main.mongodb_utils import mongodb_manager
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get filter parameters
    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    
    # Get page number
    page = request.GET.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    # Pagination settings
    per_page = 10
    
    try:
        # Get all users from MongoDB
        all_mongo_users = mongodb_manager.get_all_users()
        
        # Also get Django users for sync
        django_users = {u.username: u for u in User.objects.all()}
        
        # Format users
        formatted_users = []
        for mongo_user in all_mongo_users:
            user_dict = {
                'id': str(mongo_user.get('_id')),
                'username': mongo_user.get('username', ''),
                'email': mongo_user.get('email', ''),
                'first_name': mongo_user.get('first_name', ''),
                'last_name': mongo_user.get('last_name', ''),
                'is_active': mongo_user.get('is_active', True),
                'is_staff': mongo_user.get('is_staff', False),
                'is_superuser': mongo_user.get('is_superuser', False),
                'date_joined': mongo_user.get('date_joined'),
                'last_login': mongo_user.get('last_login'),
                'phone': mongo_user.get('phone', ''),
            }
            
            # Sync with Django user if exists
            if user_dict['username'] in django_users:
                django_user = django_users[user_dict['username']]
                user_dict['django_user_id'] = django_user.id
            
            formatted_users.append(user_dict)
        
        # Apply search filter
        if search_query:
            search_lower = search_query.lower()
            formatted_users = [
                u for u in formatted_users
                if search_lower in u.get('username', '').lower() or
                   search_lower in u.get('email', '').lower() or
                   search_lower in (u.get('first_name', '') or '').lower() or
                   search_lower in (u.get('last_name', '') or '').lower()
            ]
        
        # Apply role filter
        if role_filter:
            if role_filter == 'admin':
                formatted_users = [u for u in formatted_users if u.get('is_staff') or u.get('is_superuser')]
            elif role_filter == 'normal':
                formatted_users = [u for u in formatted_users if not u.get('is_staff') and not u.get('is_superuser')]
        
        total = len(formatted_users)
        
        # Manual pagination
        start = (page - 1) * per_page
        end = start + per_page
        users = formatted_users[start:end]
        
    except Exception as e:
        users = []
        total = 0
        messages.error(request, f'Error loading users: {str(e)}')
    
    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages
    
    context = {
        'users': users,
        'active_page': 'users',
        'search_query': search_query,
        'role_filter': role_filter,
        'current_page': page,
        'total_pages': total_pages,
        'total': total,
        'has_prev': has_prev,
        'has_next': has_next,
        'per_page': per_page,
    }
    return render(request, 'dashboard/users_list.html', context)

@login_required
def user_create(request):
    """Create a new user"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    from main.mongodb_utils import mongodb_manager
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            # Handle checkboxes - Django sends 'true' if checked, 'false' if unchecked (via hidden input)
            # If checkbox is checked, both 'true' and 'false' are sent, but 'true' comes last
            is_active_vals = request.POST.getlist('is_active')
            is_active = 'true' in is_active_vals if is_active_vals else False
            
            is_staff_vals = request.POST.getlist('is_staff')
            is_staff = 'true' in is_staff_vals if is_staff_vals else False
            
            is_superuser_vals = request.POST.getlist('is_superuser')
            is_superuser = 'true' in is_superuser_vals if is_superuser_vals else False
            
            # Validation
            errors = []
            
            if not username or len(username) < 3:
                errors.append('Username must be at least 3 characters long.')
            
            if not email or '@' not in email:
                errors.append('Please enter a valid email address.')
            
            if not password or len(password) < 8:
                errors.append('Password must be at least 8 characters long.')
            
            # Check if username already exists
            if mongodb_manager.get_user_by_username(username):
                errors.append('Username already exists.')
            
            # Check if email already exists (in both MongoDB and SQLite)
            if mongodb_manager.get_user_by_email(email):
                errors.append('Email already exists.')
            
            # Check SQLite
            if User.objects.filter(email=email).exists():
                errors.append('Email already exists in system.')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                # Preserve form data
                form_user = {
                    'username': username,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'is_active': is_active,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                }
            else:
                try:
                    # Create user data
                    user_data = {
                        'username': username,
                        'email': email,
                        'password': password,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'is_active': is_active,
                        'is_staff': is_staff,
                        'is_superuser': is_superuser,
                    }
                    
                    # Create Django User
                    django_user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=is_active,
                        is_staff=is_staff,
                        is_superuser=is_superuser,
                    )
                    
                    # Create MongoDB user
                    user_id = mongodb_manager.create_user(user_data)
                    
                    if user_id:
                        messages.success(request, '✅ User created successfully!')
                        return redirect('dashboard:users_list')
                    else:
                        messages.error(request, 'Failed to create user in MongoDB.')
                        django_user.delete()  # Rollback Django user
                except Exception as e:
                    messages.error(request, f'❌ Error creating user: {str(e)}')
                    form_user = {
                        'username': username,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'is_active': is_active,
                        'is_staff': is_staff,
                        'is_superuser': is_superuser,
                    }
        except Exception as e:
            messages.error(request, f'❌ Error creating user: {str(e)}')
            form_user = {}
    
    # Use form_user if it exists (on error), otherwise empty dict for new user
    if 'form_user' not in locals():
        form_user = {
            'username': '',
            'email': '',
            'first_name': '',
            'last_name': '',
            'phone': '',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
        }
    
    context = {
        'user': form_user,
        'active_page': 'users'
    }
    return render(request, 'dashboard/user_form.html', context)

@login_required
def user_edit(request, user_id):
    """Edit an existing user"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    from main.mongodb_utils import mongodb_manager
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get user from MongoDB
    mongo_user = mongodb_manager.get_user_by_id(user_id)
    if not mongo_user:
        messages.error(request, 'User not found')
        return redirect('dashboard:users_list')
    
    # Get Django user if exists
    django_user = None
    try:
        django_user = User.objects.get(username=mongo_user.get('username'))
    except User.DoesNotExist:
        pass
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            # Handle checkboxes - Django sends 'true' if checked, 'false' if unchecked (via hidden input)
            # If checkbox is checked, both 'true' and 'false' are sent, but 'true' comes last
            is_active_vals = request.POST.getlist('is_active')
            is_active = 'true' in is_active_vals if is_active_vals else False
            
            is_staff_vals = request.POST.getlist('is_staff')
            is_staff = 'true' in is_staff_vals if is_staff_vals else False
            
            is_superuser_vals = request.POST.getlist('is_superuser')
            is_superuser = 'true' in is_superuser_vals if is_superuser_vals else False
            
            # Validation
            errors = []
            
            # Check if username changed and already exists
            if username != mongo_user.get('username'):
                if mongodb_manager.get_user_by_username(username):
                    errors.append('Username already exists.')
            
            # Check if email changed and already exists (in both MongoDB and SQLite)
            if email != mongo_user.get('email'):
                # Check MongoDB
                if mongodb_manager.get_user_by_email(email):
                    errors.append('Email already exists.')
                
                # Check SQLite (exclude current user if exists)
                if django_user:
                    existing_user = User.objects.filter(email=email).exclude(id=django_user.id).first()
                else:
                    existing_user = User.objects.filter(email=email).first()
                
                if existing_user:
                    errors.append('Email already exists in system.')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                form_user = {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'is_active': is_active,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                }
            else:
                try:
                    # Update MongoDB user
                    update_data = {
                        'username': username,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'is_active': is_active,
                        'is_staff': is_staff,
                        'is_superuser': is_superuser,
                    }
                    
                    # Update password if provided
                    if password:
                        update_data['password'] = password
                    
                    mongodb_manager.update_user(user_id, update_data)
                    
                    # Update Django user
                    if django_user:
                        django_user.username = username
                        # Only update email if it changed (to avoid UNIQUE constraint issues)
                        if email != django_user.email:
                            django_user.email = email
                            django_user.first_name = first_name
                            django_user.last_name = last_name
                            django_user.is_active = is_active
                            django_user.is_staff = is_staff
                            django_user.is_superuser = is_superuser
                        if password:
                            django_user.set_password(password)
                        django_user.save()
                    else:
                        # Create Django user if doesn't exist
                        # Check if user with this email already exists in SQLite
                        existing_django_user = User.objects.filter(email=email).first()
                        if existing_django_user:
                            # Update existing Django user instead of creating new one
                            django_user = existing_django_user
                            django_user.username = username
                            django_user.first_name = first_name
                            django_user.last_name = last_name
                            django_user.is_active = is_active
                            django_user.is_staff = is_staff
                            django_user.is_superuser = is_superuser
                            if password:
                                django_user.set_password(password)
                            django_user.save()
                        else:
                            # Create new Django user
                            django_user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password or 'temp_password_123',
                            first_name=first_name,
                            last_name=last_name,
                            is_active=is_active,
                            is_staff=is_staff,
                            is_superuser=is_superuser,
                        )
                        if password:
                            django_user.set_password(password)
                            django_user.save()
                    
                    messages.success(request, '✅ User updated successfully!')
                    return redirect('dashboard:users_list')
                except Exception as e:
                    messages.error(request, f'❌ Error updating user: {str(e)}')
                    form_user = {
                        'id': user_id,
                        'username': username,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'is_active': is_active,
                        'is_staff': is_staff,
                        'is_superuser': is_superuser,
                    }
        except Exception as e:
            messages.error(request, f'❌ Error updating user: {str(e)}')
            form_user = {
                'id': user_id,
                'username': mongo_user.get('username', ''),
                'email': mongo_user.get('email', ''),
                'first_name': mongo_user.get('first_name', ''),
                'last_name': mongo_user.get('last_name', ''),
                'phone': mongo_user.get('phone', ''),
                'is_active': mongo_user.get('is_active', True),
                'is_staff': mongo_user.get('is_staff', False),
                'is_superuser': mongo_user.get('is_superuser', False),
            }
    
    # Use form_user if it exists (on error), otherwise use mongo_user
    if 'form_user' not in locals():
        form_user = {
            'id': user_id,
            'username': mongo_user.get('username', ''),
            'email': mongo_user.get('email', ''),
            'first_name': mongo_user.get('first_name', ''),
            'last_name': mongo_user.get('last_name', ''),
            'phone': mongo_user.get('phone', ''),
            'is_active': mongo_user.get('is_active', True),
            'is_staff': mongo_user.get('is_staff', False),
            'is_superuser': mongo_user.get('is_superuser', False),
        }
    
    context = {
        'user': form_user,
        'active_page': 'users'
    }
    return render(request, 'dashboard/user_form.html', context)

@login_required
def user_toggle_status(request, user_id):
    """Toggle user active/inactive status (enable/disable)"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Prevent disabling yourself
    from main.mongodb_utils import mongodb_manager
    mongo_user = mongodb_manager.get_user_by_id(user_id)
    if mongo_user and mongo_user.get('username') == request.user.username:
        messages.error(request, 'You cannot disable your own account.')
        return redirect('dashboard:users_list')
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        # Toggle is_active status
        new_status = not mongo_user.get('is_active', True)
        
        # Update MongoDB user
        update_data = {'is_active': new_status}
        mongodb_manager.update_user(user_id, update_data)
        
        # Update Django user if exists
        if mongo_user:
            try:
                django_user = User.objects.get(username=mongo_user.get('username'))
                django_user.is_active = new_status
                django_user.save()
            except User.DoesNotExist:
                pass
        
        status_text = 'enabled' if new_status else 'disabled'
        messages.success(request, f'User {status_text} successfully!')
    except Exception as e:
        messages.error(request, f'Error toggling user status: {str(e)}')
    
    return redirect('dashboard:users_list')

# FAQ Management Views
@login_required
def faqs_list(request):
    """Display list of all FAQs"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Fetch FAQs from MongoDB
    from main.mongodb_utils import mongodb_manager
    try:
        faqs_data = mongodb_manager.list_faqs(is_active=None)  # Get all FAQs
        # Convert to FAQ-like objects for template compatibility
        class FAQObject:
            def __init__(self, data):
                self.id = data.get('id')
                self.question = data.get('question', '')
                self.answer = data.get('answer', '')
                self.category = data.get('category', 'general')
                self.keywords = data.get('keywords', [])
                self.order = data.get('order', 0)
                self.is_active = data.get('is_active', True)
        
        faqs = [FAQObject(f) for f in faqs_data] if faqs_data else []
    except Exception as e:
        messages.error(request, f'Error loading FAQs from MongoDB: {str(e)}')
        faqs = []
    
    context = {
        'faqs': faqs,
        'active_page': 'faqs'
    }
    return render(request, 'dashboard/faqs_list.html', context)

@login_required
def faq_create(request):
    """Create a new FAQ"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Fetch FAQs from MongoDB
    from main.mongodb_utils import mongodb_manager
    
    if request.method == 'POST':
        try:
            # Get keywords from form (comma-separated)
            keywords_str = request.POST.get('keywords', '').strip()
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else []
            
            # Get order number from form
            order = request.POST.get('order', 0)
            if order:
                order = int(order)
            else:
                order = 0
            
            # Create FAQ data
            faq_data = {
                'question': request.POST.get('question', ''),
                'answer': request.POST.get('answer', ''),
                'category': request.POST.get('category', 'general'),
                'keywords': keywords,
                'order': order,
                'is_active': request.POST.get('is_active', 'true').lower() == 'true'
            }
            
            # Create FAQ in MongoDB
            faq_id = mongodb_manager.create_faq(faq_data)
            
            if faq_id:
                messages.success(request, 'FAQ created successfully!')
                return redirect('dashboard:faqs_list')
            else:
                messages.error(request, 'Error creating FAQ in MongoDB')
        except Exception as e:
            messages.error(request, f'Error creating FAQ: {str(e)}')
    
    # Get categories for dropdown
    categories = ['general', 'products', 'orders', 'payment', 'shipping', 'returns', 'account', 'support', 'privacy']
    
    context = {
        'faq': None,
        'active_page': 'faqs',
        'categories': categories
    }
    return render(request, 'dashboard/faq_form.html', context)

@login_required
def faq_edit(request, faq_id):
    """Edit an existing FAQ"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Fetch FAQ from MongoDB
    from main.mongodb_utils import mongodb_manager
    faq = mongodb_manager.get_faq_by_id(faq_id)
    
    if not faq:
        messages.error(request, 'FAQ not found')
        return redirect('dashboard:faqs_list')
    
    if request.method == 'POST':
        try:
            # Get keywords from form (comma-separated)
            keywords_str = request.POST.get('keywords', '').strip()
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else []
            
            # Get order number from form
            order = request.POST.get('order', 0)
            if order:
                order = int(order)
            else:
                order = faq.get('order', 0)
            
            # Update FAQ data
            update_data = {
                'question': request.POST.get('question', ''),
                'answer': request.POST.get('answer', ''),
                'category': request.POST.get('category', 'general'),
                'keywords': keywords,
                'order': order,
                'is_active': request.POST.get('is_active', 'true').lower() == 'true'
            }
            
            # Update FAQ in MongoDB
            success = mongodb_manager.update_faq(faq_id, update_data)
            
            if success:
                messages.success(request, 'FAQ updated successfully!')
                return redirect('dashboard:faqs_list')
            else:
                messages.error(request, 'Error updating FAQ in MongoDB')
        except Exception as e:
            messages.error(request, f'Error updating FAQ: {str(e)}')
    
    # Get categories for dropdown
    categories = ['general', 'products', 'orders', 'payment', 'shipping', 'returns', 'account', 'support', 'privacy']
    
    context = {
        'faq': faq,
        'active_page': 'faqs',
        'categories': categories
    }
    return render(request, 'dashboard/faq_form.html', context)

@login_required
def faq_delete(request, faq_id):
    """Delete a FAQ"""
    # Only allow superusers to access dashboard
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('main:home')
    
    # Delete FAQ from MongoDB
    from main.mongodb_utils import mongodb_manager
    try:
        success = mongodb_manager.delete_faq(faq_id)
        
        if success:
            messages.success(request, 'FAQ deleted successfully!')
        else:
            messages.error(request, 'Error deleting FAQ from MongoDB')
    except Exception as e:
        messages.error(request, f'Error deleting FAQ: {str(e)}')
    
    return redirect('dashboard:faqs_list')