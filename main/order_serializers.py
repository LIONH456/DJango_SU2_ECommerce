from rest_framework import serializers


class OrderSerializer(serializers.Serializer):
    """Serializer for Order (MongoDB)"""
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(allow_null=True, required=False)
    order_number = serializers.CharField(max_length=100, required=False)
    items = serializers.ListField(required=False, allow_empty=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    status = serializers.CharField(max_length=50, required=False)
    payment_status = serializers.CharField(max_length=50, required=False)
    shipping_address = serializers.DictField(required=False, allow_null=True)
    billing_address = serializers.DictField(required=False, allow_null=True)
    notes = serializers.CharField(allow_blank=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

