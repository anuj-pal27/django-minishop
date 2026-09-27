"""1C-6 tests for catalog: permissions, validation, filters, custom actions (8 tests)."""
from decimal import Decimal

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Product
from config.factories import make_category, make_product, make_staff, make_user

LIST_URL = reverse("catalog:v1-product-list")       # /api/v1/products/  (basename + "-list")


def detail_url(slug, action=None):                   # /api/v1/products/<slug>/  or  .../<slug>/restock/
    name = f"catalog:v1-product-{action}" if action else "catalog:v1-product-detail"
    return reverse(name, kwargs={"slug": slug})


class ProductPermissionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.category = make_category("hats")
        self.data = {"name": "Straw hat", "slug": "straw-hat", "price": "299.00", "stock": 5, "category": "hats"}

    def test_anyone_can_list_active_products_paged(self):
        make_product(name="Visible")
        make_product(name="Hidden", is_active=False)             # inactive = not in the API
        res = self.client.get(LIST_URL)                          # no login at all

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)                   # paged response: count/next/previous/results
        self.assertEqual(res.data["results"][0]["name"], "Visible")

    def test_anonymous_cannot_create(self):
        res = self.client.post(LIST_URL, self.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)  # 401 = "who are you?"

    def test_customer_cannot_create(self):
        self.client.force_authenticate(make_user())
        res = self.client.post(LIST_URL, self.data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)     # 403 = "I know you, but no"

    def test_staff_can_create(self):
        self.client.force_authenticate(make_staff())
        res = self.client.post(LIST_URL, self.data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(slug="straw-hat").exists())  # check the DB, not only the response


class ProductBehaviourTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client.force_authenticate(make_staff())

    def test_cheap_electronics_are_rejected(self):
        make_category("electronics")                            # seeded by migration 0003; get_or_create reuses it
        data = {"name": "Cheap cable", "slug": "cheap-cable", "price": "50.00", "category": "electronics"}
        res = self.client.post(LIST_URL, data)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", res.data)                         # our validate() puts the error on "price"

    def test_filter_by_category_and_order_by_price(self):
        hats, bags = make_category("hats"), make_category("bags")
        make_product(category=hats, name="Cheap hat", price=Decimal("100"))
        make_product(category=hats, name="Dear hat", price=Decimal("900"))
        make_product(category=bags, name="Bag", price=Decimal("500"))

        res = self.client.get(LIST_URL, {"category": "hats", "ordering": "-price"})  # dict -> ?category=hats&...
        names = [p["name"] for p in res.data["results"]]

        self.assertEqual(names, ["Dear hat", "Cheap hat"])      # only hats, most expensive first

    def test_restock_adds_stock_and_validates_amount(self):
        product = make_product(stock=2)
        url = detail_url(product.slug, "restock")

        res = self.client.post(url, {"amount": 5})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        product.refresh_from_db()                                # reload: the object in memory is old
        self.assertEqual(product.stock, 7)

        res = self.client.post(url, {"amount": 0})               # min_value=1
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_out_of_stock_is_paged(self):
        for _ in range(12):
            make_product(stock=0)
        make_product(stock=3)                                    # in stock: must not appear

        res = self.client.get(reverse("catalog:v1-product-out-of-stock"))

        self.assertEqual(res.data["count"], 12)                  # all 12 counted...
        self.assertEqual(len(res.data["results"]), 10)           # ...but only one page (page_size=10) sent
