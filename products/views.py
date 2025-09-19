from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer
from rest_framework import viewsets, permissions
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import F

@api_view(["GET"])
def category_list(request):
    """
    Returns distinct categories and subcategories from products.
    """
    categories = Product.objects.values_list("category", flat=True).distinct()
    subcategories = Product.objects.values_list("subCategory", flat=True).distinct()

    # Filter out empty values (since you allowed blank=True in model)
    categories = [c for c in categories if c]
    subcategories = [s for s in subcategories if s]

    return Response({
        "categories": categories,
        "subcategories": subcategories,
    })

# serialize the data and create API views
class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


# Step 2: custom permission
class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

# Product ViewSet
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]


def products_page(request):
    products = Product.objects.all()
    categories = Product.objects.values_list('category', flat=True).distinct()
    return render(request, 'products/home.html', {
        'products': products,
        'categories': categories,
    })

from django.shortcuts import render

def cart_view(request):
    return render(request, "products/cart.html")

def view_more(request, pk):
    product = get_object_or_404(Product, pk=pk)
    similar_products = Product.objects.filter(subCategory=product.subCategory).exclude(id=product.id)[:10]
    return render(request, "products/view_more.html", {
        "product": product,
        "similar_products": similar_products
    })