from django.urls import path

from . import views

app_name = "catalog"                              # lets us write "catalog:product-list"

urlpatterns = [
    # function-based
    path("fbv/products/", views.product_list, name="fbv-product-list"),
    path("fbv/products/<slug:slug>/", views.product_detail, name="fbv-product-detail"),
    # class-based: .as_view() turns the class into a function Django can call
    path("ping/", views.PingView.as_view(), name="ping"),
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("categories/<slug:slug>/", views.CategoryProductListView.as_view(), name="category-products"),
]
