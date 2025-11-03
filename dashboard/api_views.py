from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Slider
from .serializers import SliderSerializer, SliderCreateSerializer, SliderUpdateSerializer


class SliderViewSet(viewsets.ModelViewSet):
    """ViewSet for Slider model"""
    queryset = Slider.objects.all().order_by('order')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SliderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SliderUpdateSerializer
        return SliderSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def active(self, request):
        """Get active sliders (public endpoint)"""
        sliders = Slider.objects.filter(status='active').order_by('order')
        serializer = self.get_serializer(sliders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle slider status"""
        slider = self.get_object()
        slider.status = 'inactive' if slider.status == 'active' else 'active'
        slider.save()
        serializer = self.get_serializer(slider)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder sliders"""
        items = request.data.get('items', [])
        if not items:
            return Response(
                {'error': 'No items provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # First, update all sliders to temporary high order numbers
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
            
            return Response({'success': True})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

