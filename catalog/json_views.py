import json
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Category, Product


def product_to_dict(product):                     # model -> dict, written BY HAND for every field
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "price": str(product.price),              # Decimal can't go into JSON directly -> string
        "stock": product.stock,
        "category": product.category.slug,
    }


@csrf_exempt                                      # turn off CSRF check (unsafe; DRF does it properly in 1C)
@require_http_methods(["GET", "POST"])            # any other method -> 405
def products_api(request):
    # ----- GET: list products -----
    if request.method == "GET":
        products = Product.objects.filter(is_active=True).select_related("category")
        return JsonResponse({"results": [product_to_dict(p) for p in products]})

    # ----- POST: create a product -----
    try:
        data = json.loads(request.body)           # raw body text -> Python dict
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    errors = {}                                   # collect ALL errors, check everything by hand

    for field in ["name", "slug", "price", "category"]:
        if not data.get(field):
            errors[field] = "This field is required."

    price = None
    if "price" not in errors:                     # fix #3: only check the number if it was given
        try:
            price = Decimal(str(data["price"]))   # text -> Decimal
            if price <= 0:
                errors["price"] = "Must be greater than 0."
        except InvalidOperation:                  # not a number
            errors["price"] = "Must be a number."

    stock = data.get("stock", 0)                  # fix #2 (exercise): validate stock
    if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:  # bool is an int in Python!
        errors["stock"] = "Must be a whole number, 0 or more."

    category = None
    if "category" not in errors:
        category = Category.objects.filter(slug=data["category"]).first()  # None if not found
        if category is None:
            errors["category"] = "Unknown category."

    if data.get("slug") and Product.objects.filter(slug=data["slug"]).exists():
        errors["slug"] = "A product with this slug already exists."

    if errors:
        return JsonResponse({"errors": errors}, status=400)   # 400 = your data is wrong

    product = Product.objects.create(
        name=data["name"],
        slug=data["slug"],
        price=price,
        stock=stock,
        category=category,
    )
    product.refresh_from_db()                     # fix #1: reload, so price comes back as "299.00"
    return JsonResponse(product_to_dict(product), status=201)  # 201 = created


@require_http_methods(["GET"])
def product_detail_api(request, slug):
    product = Product.objects.select_related("category").filter(slug=slug, is_active=True).first()
    if product is None:
        return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse(product_to_dict(product))
