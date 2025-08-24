from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Slider
from django.db import models

# Create your views here.
@login_required
def index(request):
    context = {
        'active_page': 'dashboard'
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def sliders_list(request):
    """Display list of all sliders"""
    sliders = Slider.objects.all()
    context = {
        'sliders': sliders,
        'active_page': 'sliders'
    }
    return render(request, 'dashboard/Sliders.html', context)

@login_required
def slider_create(request):
    """Create a new slider"""
    if request.method == 'POST':
        try:
            # Get the order number from form
            order = request.POST.get('order', 0)
            if order:
                order = int(order)
            else:
                # Auto-assign order number (next available)
                order = Slider.get_next_order()
            
            # Check if order number already exists
            existing_slider = Slider.objects.filter(order=order).first()
            if existing_slider:
                # Shift existing sliders to make room
                Slider.objects.filter(order__gte=order).update(order=models.F('order') + 1)
            
            slider = Slider.objects.create(
                title=request.POST.get('title', ''),
                subtitle=request.POST.get('subtitle', ''),
                description=request.POST.get('description', ''),
                img=request.POST.get('img', ''),
                link=request.POST.get('link', ''),
                status=request.POST.get('status', 'active'),
                order=order
            )
            messages.success(request, 'Slider created successfully!')
            return redirect('dashboard:sliders_list')
        except Exception as e:
            messages.error(request, f'Error creating slider: {str(e)}')
    
    # Get next available order number for the form
    next_order = Slider.get_next_order()
    
    context = {
        'slider': None,
        'active_page': 'sliders',
        'next_order': next_order
    }
    return render(request, 'dashboard/slider_form.html', context)

@login_required
def slider_edit(request, slider_id):
    """Edit an existing slider"""
    slider = get_object_or_404(Slider, id=slider_id)
    
    if request.method == 'POST':
        try:
            old_order = slider.order
            new_order = request.POST.get('order', 0)
            if new_order:
                new_order = int(new_order)
            else:
                new_order = old_order
            
            # Check if order number changed and conflicts with existing
            if new_order != old_order:
                existing_slider = Slider.objects.filter(order=new_order).exclude(id=slider_id).first()
                if existing_slider:
                    # Shift existing sliders to make room
                    if new_order > old_order:
                        # Moving to higher order - shift sliders between old and new
                        Slider.objects.filter(order__gt=old_order, order__lte=new_order).exclude(id=slider_id).update(order=models.F('order') - 1)
                    else:
                        # Moving to lower order - shift sliders between new and old
                        Slider.objects.filter(order__gte=new_order, order__lt=old_order).exclude(id=slider_id).update(order=models.F('order') + 1)
            
            slider.title = request.POST.get('title', '')
            slider.subtitle = request.POST.get('subtitle', '')
            slider.description = request.POST.get('description', '')
            slider.img = request.POST.get('img', '')
            slider.link = request.POST.get('link', '')
            slider.status = request.POST.get('status', 'active')
            slider.order = new_order
            slider.save()
            
            messages.success(request, 'Slider updated successfully!')
            return redirect('dashboard:sliders_list')
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
    slider = get_object_or_404(Slider, id=slider_id)
    try:
        order_to_delete = slider.order
        slider.delete()
        
        # Reorder remaining sliders
        Slider.objects.filter(order__gt=order_to_delete).update(order=models.F('order') - 1)
        
        messages.success(request, 'Slider deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting slider: {str(e)}')
    
    return redirect('dashboard:sliders_list')

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def slider_toggle_status(request, slider_id):
    """Toggle slider status via AJAX"""
    try:
        slider = get_object_or_404(Slider, id=slider_id)
        slider.status = 'inactive' if slider.status == 'active' else 'active'
        slider.save()
        
        return JsonResponse({
            'success': True,
            'status': slider.status
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
    """Reorder sliders via AJAX"""
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        
        # First, update all sliders to temporary high order numbers to avoid conflicts
        temp_start = 10000
        for i, item in enumerate(items):
            slider_id = item.get('id')
            if slider_id:
                Slider.objects.filter(id=slider_id).update(order=temp_start + i)
        
        # Then update to final order numbers
        for i, item in enumerate(items):
            slider_id = item.get('id')
            final_order = item.get('order')
            if slider_id and final_order is not None:
                Slider.objects.filter(id=slider_id).update(order=final_order)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })