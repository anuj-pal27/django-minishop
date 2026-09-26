from rest_framework import viewsets

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.select_related("user").prefetch_related("items__product")
    serializer_class = OrderSerializer
