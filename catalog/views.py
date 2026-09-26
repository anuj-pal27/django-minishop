from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Category, Product


# ---------- Function-based views (FBV) ----------

def product_list(request):                        # request = everything about the browser's request
    products = Product.objects.filter(is_active=True).select_related("category")
    return render(request, "catalog/product_list.html", {"products": products})  # fill template, send back


def product_detail(request, slug):                # slug comes from the URL: /fbv/products/<slug>/
    product = get_object_or_404(Product, slug=slug, is_active=True)  # not found -> 404 page
    return render(request, "catalog/product_detail.html", {"product": product})


# ---------- Class-based views (CBV) ----------

class PingView(View):                             # simplest CBV: one method per HTTP method
    def get(self, request):
        return HttpResponse("pong (GET)")

    def post(self, request):
        return HttpResponse("pong (POST)")


class ProductListView(ListView):                  # ListView = "show a list of rows"
    template_name = "catalog/product_list.html"
    context_object_name = "products"              # name used in the template
    paginate_by = 10                              # 10 per page, for free

    def get_queryset(self):                       # which rows to show
        return Product.objects.filter(is_active=True).select_related("category")


class ProductDetailView(DetailView):              # DetailView = "show one row" (404 if missing)
    queryset = Product.objects.filter(is_active=True)
    template_name = "catalog/product_detail.html"
    context_object_name = "product"


class CategoryProductListView(ListView):          # exercise: products of ONE category
    template_name = "catalog/product_list.html"   # reuse the same list template
    context_object_name = "products"
    paginate_by = 10

    def get_queryset(self):
        # self.kwargs = values captured from the URL, here {"slug": "..."}
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])  # unknown category -> 404
        return self.category.products.filter(is_active=True)  # related_name="products" (1A-2)

    def get_context_data(self, **kwargs):          # extra data for the template
        context = super().get_context_data(**kwargs)
        context["category"] = self.category       # so the page can show the category name
        return context
