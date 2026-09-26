from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import viewsets

app_name = "orders"

router = DefaultRouter()
router.register("orders", viewsets.OrderViewSet, basename="v1-order")

urlpatterns = [
    path("api/v1/", include(router.urls)),
]
