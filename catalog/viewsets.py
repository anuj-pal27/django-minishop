from django.db.models import F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, RestockSerializer

class CategoryViewSet(viewsets.ModelViewSet):         # ModelViewSet = list+create+get+update+delete
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"                             # /categories/shoes/ instead of /categories/1/
    # ↑ that's your 1B-2 exercise, done in 3 lines

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related("category")
    serializer_class = ProductSerializer
    lookup_field = "slug"

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
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)