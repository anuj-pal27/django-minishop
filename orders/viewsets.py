from rest_framework import permissions, viewsets

from users.permissions import IsOwnerOrStaff

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]  # ALL must pass

    def get_queryset(self):                                   # replaces "queryset = ..."
        qs = Order.objects.select_related("user").prefetch_related("items__product")
        if self.request.user.is_staff:
            return qs                                         # staff: every order
        return qs.filter(user=self.request.user)              # customer: only their own
