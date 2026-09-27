from django.db.models import F
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from .filters import ProductFilter
from django_filters.rest_framework import DjangoFilterBackend
from users.permissions import IsStaffOrReadOnly

from .models import Category, Product
from .serializers import CategorySerializer, ProductListSerializer, ProductSerializer, RestockSerializer
from config.pagination import StandardLimitOffsetPagination

class CategoryViewSet(viewsets.ModelViewSet):         # ModelViewSet = list+create+get+update+delete
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]           # anyone reads, only staff writes
    pagination_class = StandardLimitOffsetPagination
    lookup_field = "slug"                             # /categories/shoes/ instead of /categories/1/
    # ↑ that's your 1B-2 exercise, done in 3 lines

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related("category")
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]           # restock is a POST, so staff only too
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name","description","category__name"]
    ordering_fields = ["price", "name", "created_at", "stock"]
    ordering = ["-created_at"]                       # default order (1C-6: typo "ordeing" fixed)
    lookup_field = "slug"

    def get_serializer_class(self):                   # pick a serializer per action
        if self.action == "list":                     # GET /products/ -> short version
            return ProductListSerializer
        return ProductSerializer                      # everything else -> full version

    def get_throttles(self):                          # pick limiters per action (1C-5 exercise)
        if self.action == "restock":
            self.throttle_scope = "restock"           # uses the "restock" rate: 10/hour
            return [ScopedRateThrottle()]
        return super().get_throttles()                # other actions: normal anon/user limits

    # ----- custom action on ONE product: POST /products/<slug>/restock/ -----
    @action(detail=True, methods=["post"])            # detail=True → needs a slug in the URL
    def restock(self, request, slug=None):
        product = self.get_object()                   # finds the product by slug, or 404
        input_serializer = RestockSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)          # bad amount → 400
        amount = input_serializer.validated_data["amount"]

        Product.objects.filter(pk=product.pk).update(stock=F("stock") + amount)  # safe add (1A-4!)
        product.refresh_from_db()                     # reload the new stock value
        return Response(self.get_serializer(product).data)

    # ----- custom action on the LIST: GET /products/out-of-stock/ -----
    @action(detail=False, methods=["get"], url_path="out-of-stock")  # detail=False → no slug
    def out_of_stock(self, request):
        products = self.get_queryset().filter(stock=0)
        page = self.paginate_queryset(products)  #cut out the current page
        serializer = self.get_serializer(page, many=True)  # 1C-6 fix: serialize the PAGE, not all rows
        return self.get_paginated_response(serializer.data)   # adds count/next/previous