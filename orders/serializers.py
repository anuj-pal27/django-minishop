from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "quantity", "unit_price"]
        # The model's UniqueConstraint(order, product) automatically adds a
        # "same product twice in one order" check. No code needed here.


class OrderItemReadSerializer(serializers.ModelSerializer):    # how ONE item looks inside an order
    product = serializers.CharField(source="product.name")    # show the name, not the id
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "unit_price", "line_total"]

    def get_line_total(self, obj):
        return str(obj.quantity * obj.unit_price)             # str() keeps Decimal exact in JSON


class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.EmailField(source="user.email", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)  # source can call a method
    items = OrderItemReadSerializer(many=True, read_only=True)  # nested list (related_name="items")
    item_count = serializers.IntegerField(source="items.count", read_only=True)  # 1B-5 exercise
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "customer", "status", "status_label", "created_at", "items", "item_count", "total"]

    def get_total(self, obj):
        return str(sum(item.quantity * item.unit_price for item in obj.items.all()))
