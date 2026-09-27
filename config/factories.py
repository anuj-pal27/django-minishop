"""Tiny test "factories" (1C-6): one function per model that builds a valid object fast.

Each test only passes the fields it cares about; everything else gets a safe default.
(The library factory_boy does the same thing with more features; plain functions are enough for now.)
"""
from decimal import Decimal
from itertools import count

from django.contrib.auth import get_user_model

from catalog.models import Category, Product
from orders.models import Order, OrderItem

User = get_user_model()
_n = count(1)                                       # 1, 2, 3... so every email/slug is unique

PASSWORD = "S3cure-pass-123"                        # passes Django's password validators


def make_user(**kwargs):
    kwargs.setdefault("email", f"user{next(_n)}@example.com")
    return User.objects.create_user(password=PASSWORD, **kwargs)   # create_user hashes the password


def make_staff(**kwargs):
    return make_user(is_staff=True, **kwargs)


def make_category(slug=None, **kwargs):
    slug = slug or f"cat-{next(_n)}"
    kwargs.setdefault("name", slug.title())
    # get_or_create: migration 0003 already seeded shoes/clothing/electronics in the test DB
    category, _ = Category.objects.get_or_create(slug=slug, defaults=kwargs)
    return category


def make_product(**kwargs):
    kwargs.setdefault("category", make_category())
    n = next(_n)
    kwargs.setdefault("name", f"Product {n}")
    kwargs.setdefault("slug", f"product-{n}")
    kwargs.setdefault("price", Decimal("499.00"))
    kwargs.setdefault("stock", 10)
    return Product.objects.create(**kwargs)


def make_order(user, items=(), **kwargs):
    """items = [(product, quantity), ...]; unit_price is copied from the product."""
    order = Order.objects.create(user=user, **kwargs)
    for product, quantity in items:
        OrderItem.objects.create(order=order, product=product, quantity=quantity, unit_price=product.price)
    return order
