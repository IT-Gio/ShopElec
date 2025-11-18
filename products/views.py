from rest_framework import generics, viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.db.models import Avg, Q
from .models import Product, Category
from .serializers import ProductSerializer
from django.core.paginator import Paginator
from django.shortcuts import render, redirect

# ---------------- HOME VIEW ----------------
from django.shortcuts import render, redirect
from django.db.models import Avg, Q
from django.core.paginator import Paginator
from .models import Product, Category

# ---------------- HOME VIEW ----------------
def stars10to5_py(avg_rating):
    """
    Converts a 10-point rating to a list of 5 stars: 'full', 'half', 'empty'.
    """
    try:
        avg_rating = float(avg_rating)
    except (ValueError, TypeError):
        return ["empty"] * 5

    stars = []
    five_scale = avg_rating / 2
    for i in range(1, 6):
        if five_scale >= i:
            stars.append("full")
        elif five_scale >= i - 0.5:
            stars.append("half")
        else:
            stars.append("empty")
    return stars

def home(request):
    sort = request.GET.get("sort")
    category = request.GET.get("category")
    query = request.GET.get("q")

    if request.GET.get("clear"):
        return redirect("home")

    # --- Base queryset ---
    products_qs = Product.objects.all()

    # --- SEARCH ---
    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query)
        ).distinct()

    # --- CATEGORY FILTER ---
    if category and category.lower() != "none":
        products_qs = products_qs.filter(category__name=category)

    # --- SORTING ---
    if sort == "price-asc":
        products_qs = products_qs.order_by("price")
    elif sort == "price-desc":
        products_qs = products_qs.order_by("-price")
    elif sort == "rating":
        products_qs = products_qs.annotate(latest_avg=Avg("order_reviews__rating")).order_by("-latest_avg")
    elif sort == "AZ":
        products_qs = products_qs.order_by("name")
    elif sort == "ZA":
        products_qs = products_qs.order_by("-name")

    # --- PAGINATION ---
    paginator = Paginator(products_qs, 10)
    page = request.GET.get("page")
    products_page = paginator.get_page(page)

    # --- Precompute latest stars using order_reviews ---
    product_ids = [p.id for p in products_page]
    latest_ratings = (
        Product.objects.filter(id__in=product_ids)
        .annotate(avg_rating=Avg("order_reviews__rating"))
        .values("id", "avg_rating")
    )
    rating_map = {item["id"]: item["avg_rating"] or 0 for item in latest_ratings}

    for product in products_page:
        avg = rating_map.get(product.id, 0)
        product.stars = stars10to5_py(avg)

    categories = Category.objects.values_list("name", flat=True).distinct()

    return render(request, "products/home.html", {
        "products": products_page,
        "categories": categories,
        "page_obj": products_page,
        "selected_sort": sort,
        "selected_category": category,
        "search_query": query,
    })

# ---------------- API: Categories ----------------
@api_view(["GET"])
def category_list(request):
    """
    Returns distinct categories and subcategories from products.
    """
    categories = Product.objects.values_list("category", flat=True).distinct()
    subcategories = Product.objects.values_list("subCategory", flat=True).distinct()

    categories = [c for c in categories if c]
    subcategories = [s for s in subcategories if s]

    return Response({
        "categories": categories,
        "subcategories": subcategories,
    })


# ---------------- API: Products ----------------
class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.annotate(avg_rating=Avg("product_reviews__rating"))
    serializer_class = ProductSerializer


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.annotate(avg_rating=Avg("product_reviews__rating"))
    serializer_class = ProductSerializer


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user and request.user.is_authenticated and request.user.is_staff)
        )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.annotate(avg_rating=Avg("product_reviews__rating"))
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]


# ---------------- TEMPLATE VIEWS ----------------
def products_page(request):
    products = Product.objects.annotate(avg_rating=Avg("product_reviews__rating"))
    categories = Product.objects.values_list('category', flat=True).distinct()
    return render(request, 'products/home.html', {
        'products': products,
        'categories': categories,
    })


def cart_view(request):
    return render(request, "products/cart.html", {
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY
    })

