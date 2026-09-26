from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .serializers import ProductSerializer

# LEVEL 1: APIVIEW

class ProductListAPIView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_active=True).select_related("category")
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ProductSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED0
        )

class ProductDetailAPIView(APIView):
    def get_object(self, slug):                               # shared helper
        return get_object_or_404(Product, slug=slug, is_active=True)

    def get(self, request, slug):                             # GET one
        product = self.get_object(slug)
        return Response(ProductSerializer(product).data)

    def put(self, request, slug):                             # PUT = replace ALL fields
        product = self.get_object(slug)
        serializer = ProductSerializer(product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()                                     # calls update()
        return Response(serializer.data)

    def patch(self, request, slug):                           # PATCH = change SOME fields
        product = self.get_object(slug)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug):                          # DELETE
        self.get_object(slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    # 204 = done, nothing to return

# LEVEL 2: GenericAPIView + mixins

class ProductListMixinView(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           generics.GenericAPIView):
    queryset = Product.objects.filter(is_active=True).select_related("category")
    serializer_class = ProductSerializer

    def get(self,request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


# ================= Level 3: concrete generic views (we use these from now on) =================

class ProductListCreateView(generics.ListCreateAPIView):      # GET list + POST create
    queryset = Product.objects.filter(is_active=True).select_related("category")
    serializer_class = ProductSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):  # GET one + PUT + PATCH + DELETE
    queryset = Product.objects.filter(is_active=True).select_related("category")
    serializer_class = ProductSerializer
    lookup_field = "slug"                                     # find by slug instead of id