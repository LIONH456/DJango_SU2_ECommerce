from rest_framework import serializers
from .models import Slider


class SliderSerializer(serializers.ModelSerializer):
    """Serializer for Slider model"""
    is_active_property = serializers.ReadOnlyField(source='is_active')
    
    class Meta:
        model = Slider
        fields = [
            'id', 'title', 'subtitle', 'description', 'img', 'link',
            'status', 'order', 'is_active_property',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SliderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sliders"""
    
    class Meta:
        model = Slider
        fields = [
            'title', 'subtitle', 'description', 'img', 'link',
            'status', 'order'
        ]
    
    def create(self, validated_data):
        # Auto-assign order if not provided
        if 'order' not in validated_data or not validated_data['order']:
            validated_data['order'] = Slider.get_next_order()
        return super().create(validated_data)


class SliderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating sliders"""
    
    class Meta:
        model = Slider
        fields = [
            'title', 'subtitle', 'description', 'img', 'link',
            'status', 'order'
        ]

