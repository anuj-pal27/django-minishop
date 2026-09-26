from django.contrib import admin
from django.db.models import F, Sum

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at", "total")
    list_filter = ("status", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("created_at",)
    list_select_related = ("user",)
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(order_total=Sum(F("items__quantity") * F("items__unit_price")))

    @admin.display(description="Total (₹)", ordering="order_total")
    def total(self, obj):
        return obj.order_total or 0
