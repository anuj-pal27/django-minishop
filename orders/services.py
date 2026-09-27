"""1D-2: order business logic (service functions), safe against two buyers racing.

Tools used:
- transaction.atomic()  -> all-or-nothing: any error undoes every change in the block
- select_for_update()   -> locks the rows we read until the transaction ends; other buyers wait
- F("stock") - qty      -> the database does the maths, never an old number from Python
"""
from django.db import transaction
from django.db.models import F

from catalog.models import Product

from .models import Order, OrderItem


class OrderError(Exception):                     # base class: the view can catch all order errors at once
    pass


class ProductUnavailable(OrderError):            # product id doesn't exist or is not active
    pass


class OutOfStock(OrderError):                    # not enough stock for the quantity asked
    pass


class CannotCancel(OrderError):                  # order already shipped / cancelled
    pass


def place_order(user, items):
    """items = [(product_id, quantity), ...]  ->  the new Order, or raises an OrderError."""
    with transaction.atomic():                                   # all-or-nothing from here
        ids = [pid for pid, _ in items]
        products = (Product.objects
                    .select_for_update()                         # LOCK these rows; other buyers wait here
                    .filter(pk__in=ids, is_active=True)
                    .order_by("pk"))                             # same lock order every time -> no deadlocks
        by_id = {p.pk: p for p in products}                      # running the query takes the locks

        order = Order.objects.create(user=user)
        for pid, qty in items:
            product = by_id.get(pid)
            if product is None:
                raise ProductUnavailable(f"Product {pid} is not available.")
            if product.stock < qty:                              # safe: stock can't change while we hold the lock
                raise OutOfStock(f"Only {product.stock} left of {product.name}.")
            OrderItem.objects.create(order=order, product=product,
                                     quantity=qty, unit_price=product.price)  # copy the price at buy time
            Product.objects.filter(pk=pid).update(stock=F("stock") - qty)     # DB does the maths
        return order                                             # leaving the block = COMMIT + locks released
    # an exception raised inside the block = ROLLBACK: the order and its items disappear


def cancel_order(order):
    """1D-2 exercise: cancel a pending/paid order and put the stock back."""
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)   # lock the ORDER: stops a double cancel
        if order.status in (Order.Status.SHIPPED, Order.Status.CANCELLED):
            raise CannotCancel(f"Order #{order.pk} is {order.status}, it can't be cancelled.")

        for item in order.items.all():
            # no product lock needed: F() adds safely even if someone is buying at the same time
            Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)

        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])                     # only write the column we changed
        return order
