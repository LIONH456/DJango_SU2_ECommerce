from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    """Serializer for Product (MongoDB) - Full CRUD"""
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=200, allow_blank=True, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    compare_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True, required=False)
    sku = serializers.CharField(max_length=100, allow_blank=True, required=False)
    quantity = serializers.IntegerField(default=0)
    is_available = serializers.BooleanField(default=True)
    category_id = serializers.CharField(allow_null=True, required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    images = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def create(self, validated_data):
        """Create product in MongoDB"""
        from .mongodb_utils import mongodb_manager
        from decimal import Decimal
        from bson import ObjectId
        # Convert Decimal to float for MongoDB compatibility
        if 'price' in validated_data and isinstance(validated_data['price'], Decimal):
            validated_data['price'] = float(validated_data['price'])
        if 'compare_price' in validated_data and isinstance(validated_data['compare_price'], Decimal):
            validated_data['compare_price'] = float(validated_data['compare_price'])
        # Convert category_id to ObjectId if provided
        if 'category_id' in validated_data and validated_data['category_id']:
            try:
                if isinstance(validated_data['category_id'], str):
                    validated_data['category_id'] = ObjectId(validated_data['category_id'])
            except:
                validated_data['category_id'] = None
        else:
            validated_data['category_id'] = None
        product_id = mongodb_manager.create_product(validated_data)
        return mongodb_manager.get_product_by_id(product_id)
    
    def update(self, instance, validated_data):
        """Update product in MongoDB"""
        from .mongodb_utils import mongodb_manager
        from decimal import Decimal
        from bson import ObjectId
        # Convert Decimal to float for MongoDB compatibility
        if 'price' in validated_data and isinstance(validated_data['price'], Decimal):
            validated_data['price'] = float(validated_data['price'])
        if 'compare_price' in validated_data and isinstance(validated_data['compare_price'], Decimal):
            validated_data['compare_price'] = float(validated_data['compare_price'])
        # Convert category_id to ObjectId if provided
        if 'category_id' in validated_data:
            if validated_data['category_id']:
                try:
                    if isinstance(validated_data['category_id'], str):
                        validated_data['category_id'] = ObjectId(validated_data['category_id'])
                except:
                    validated_data['category_id'] = None
            else:
                validated_data['category_id'] = None
        product_id = instance.get('id') or instance.get('_id')
        mongodb_manager.update_product(product_id, validated_data)
        return mongodb_manager.get_product_by_id(product_id)

