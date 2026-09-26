from django.contrib import admin
from django.db.models import Count

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "product_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(num_products=Count("products"))

    @admin.display(description="Products", ordering="num_products")
    def product_count(self, obj):
        return obj.num_products


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "in_stock", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("name", "slug")
    list_editable = ("price", "stock", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category",)
    list_per_page = 25
    actions = ["mark_inactive"]

    @admin.display(description="In stock", boolean=True)  # boolean=True shows a ✅/❌ icon
    def in_stock(self, obj):                      # obj = one product row
        return obj.stock > 0                      # True if at least 1 item is left

    @admin.action(description="Mark selected products as inactive")
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} product(s) marked inactive.")
