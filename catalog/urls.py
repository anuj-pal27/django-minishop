from django.urls import path, include
from rest_framework.routers import DefaultRouter            # new

from . import json_views, views, api_views, viewsets

app_name = "catalog"                              # lets us write "catalog:product-list"

router = DefaultRouter()                                     # creates URLs from ViewSets
router.register("categories", viewsets.CategoryViewSet, basename="v1-category")
router.register("products", viewsets.ProductViewSet, basename="v1-product")

urlpatterns = [
    # function-based
    path("fbv/products/", views.product_list, name="fbv-product-list"),
    path("fbv/products/<slug:slug>/", views.product_detail, name="fbv-product-detail"),
    # class-based: .as_view() turns the class into a function Django can call
    path("ping/", views.PingView.as_view(), name="ping"),
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("categories/<slug:slug>/", views.CategoryProductListView.as_view(), name="category-products"),
    # plain JSON API (by hand, before DRF)
    path("api/raw/products/", json_views.products_api, name="raw-products"),
    path("api/raw/products/<slug:slug>/", json_views.product_detail_api, name="raw-product-detail"),
      # Level 1
    path("api/apiview/products/", api_views.ProductListAPIView.as_view(), name="apiview-products"),
    path("api/apiview/products/<slug:slug>/", api_views.ProductDetailAPIView.as_view(), name="apiview-product-detail"),
    # Level 2
    path("api/mixins/products/", api_views.ProductListMixinView.as_view(), name="mixins-products"),
    # Level 3
    path("api/products/", api_views.ProductListCreateView.as_view(), name="api-products"),
    path("api/products/<slug:slug>/", api_views.ProductDetailView.as_view(), name="api-product-detail"),

    path("api/v1/", include(router.urls)),                   # all router URLs under /api/v1/
]
