import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")      # ?category=shoes
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")  # price >= X
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")  # price <= X
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")      # custom logic below

    class Meta:
        model = Product
        fields = ["category", "min_price", "max_price", "in_stock"]

    def filter_in_stock(self, queryset, name, value):   # value = True or False from the URL
        if value:
            return queryset.filter(stock__gt=0)         # ?in_stock=true
        return queryset.filter(stock=0)                 # ?in_stock=false