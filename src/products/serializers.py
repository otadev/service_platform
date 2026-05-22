from rest_framework import serializers

from products.models import Order
from products.services import create_order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Сумма должна быть больше нуля')
        return value

    def create(self, validated_data):
        return create_order(**validated_data)