from rest_framework import serializers


class CategorySerializer(serializers.Serializer):
    """Serializer for Category (MongoDB)"""
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=200, allow_blank=True, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    image = serializers.CharField(allow_blank=True, required=False)
    parent_id = serializers.CharField(allow_null=True, required=False)
    is_active = serializers.BooleanField(default=True)
    sort_order = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def create(self, validated_data):
        """Create category in MongoDB"""
        from .mongodb_utils import mongodb_manager
        category_id = mongodb_manager.create_category(validated_data)
        return mongodb_manager.get_category_by_id(category_id)
    
    def update(self, instance, validated_data):
        """Update category in MongoDB"""
        from .mongodb_utils import mongodb_manager
        category_id = instance.get('id') or instance.get('_id')
        mongodb_manager.update_category(category_id, validated_data)
        return mongodb_manager.get_category_by_id(category_id)

