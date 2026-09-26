from rest_framework import serializers

from .models import OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "quantity", "unit_price"]
        # The model's UniqueConstraint(order, product) automatically adds a
        # "same product twice in one order" check. No code needed here.
