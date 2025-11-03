from rest_framework import serializers


class PaymentSerializer(serializers.Serializer):
    """Serializer for Payment (MongoDB)"""
    id = serializers.CharField(read_only=True)
    order_id = serializers.CharField(allow_null=True, required=False)
    user_id = serializers.CharField(allow_null=True, required=False)
    payment_method = serializers.CharField(max_length=50, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=10, default='USD', required=False)
    status = serializers.CharField(max_length=50, required=False)
    transaction_id = serializers.CharField(max_length=200, allow_blank=True, required=False)
    payment_date = serializers.DateTimeField(allow_null=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

