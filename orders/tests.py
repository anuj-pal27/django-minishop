"""1C-6 tests for orders: auth, own-orders-only, staff, totals, filter, read-only (7 tests)."""
from decimal import Decimal

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from config.factories import make_order, make_product, make_staff, make_user
from orders.models import Order

LIST_URL = reverse("orders:v1-order-list")          # /api/v1/orders/


def detail_url(order):
    return reverse("orders:v1-order-detail", args=[order.pk])


class OrderTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.alice, self.bob = make_user(), make_user()
        self.alice_order = make_order(self.alice)
        self.bob_order = make_order(self.bob)

    def ids(self, res):                              # small helper: order ids in a list response
        return {o["id"] for o in res.data["results"]}

    def test_anonymous_gets_401(self):
        self.assertEqual(self.client.get(LIST_URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_lists_only_own_orders(self):
        self.client.force_authenticate(self.alice)
        res = self.client.get(LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids(res), {self.alice_order.id})    # Bob's order is not there

    def test_customer_gets_404_for_someone_elses_order(self):
        self.client.force_authenticate(self.alice)
        res = self.client.get(detail_url(self.bob_order))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)  # 404, not 403: don't leak that it exists

    def test_staff_sees_every_order(self):
        self.client.force_authenticate(make_staff())
        res = self.client.get(LIST_URL)
        self.assertEqual(self.ids(res), {self.alice_order.id, self.bob_order.id})

    def test_total_and_item_count(self):
        pen = make_product(price=Decimal("10.50"))
        book = make_product(price=Decimal("200.00"))
        order = make_order(self.alice, items=[(pen, 2), (book, 1)])   # 2 x 10.50 + 1 x 200 = 221.00

        self.client.force_authenticate(self.alice)
        res = self.client.get(detail_url(order))

        self.assertEqual(res.data["item_count"], 2)
        self.assertEqual(Decimal(res.data["total"]), Decimal("221.00"))  # compare as Decimal, not float

    def test_filter_by_status(self):
        paid = make_order(self.alice, status=Order.Status.PAID)
        self.client.force_authenticate(self.alice)
        res = self.client.get(LIST_URL, {"status": "paid"})
        self.assertEqual(self.ids(res), {paid.id})                   # the pending order is filtered out

    def test_orders_api_is_read_only(self):
        self.client.force_authenticate(self.alice)
        res = self.client.post(LIST_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)  # ReadOnlyModelViewSet: no POST


class OrderQueryCountTests(APITestCase):
    """1D-1: the number of SQL queries must NOT grow with the number of orders (no N+1)."""

    def setUp(self):
        cache.clear()
        self.alice = make_user()
        self.client.force_authenticate(self.alice)      # force_authenticate: no extra "load user" query

    def make_orders(self, how_many):
        for _ in range(how_many):                        # each order has 2 items with 2 different products
            make_order(self.alice, items=[(make_product(), 2), (make_product(), 1)])

    def test_order_list_uses_3_queries(self):
        self.make_orders(5)
        # 1 = orders + users (select_related JOIN)
        # 2 = all items of those orders          (prefetch_related "items")
        # 3 = all products of those items        (prefetch_related "items__product")
        with self.assertNumQueries(3):                   # fails and prints the SQL if the count is different
            res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_query_count_does_not_grow_with_more_orders(self):
        self.make_orders(1)
        with self.assertNumQueries(3):
            self.client.get(LIST_URL)

        self.make_orders(9)                              # now 10 orders, 20 items
        with self.assertNumQueries(3):                   # still 3: this is the real N+1 check
            self.client.get(LIST_URL)

    def test_order_detail_uses_3_queries(self):
        self.make_orders(1)
        order = self.alice.orders.first()
        with self.assertNumQueries(3):
            self.client.get(detail_url(order))
