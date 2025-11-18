# shop/views.py

from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from products.models import Product
from .models import CartItem
from .utils import get_user_cart
from .serializers import CartItemSerializer


# ==========================
# 🔹 API VIEWS
# ==========================

@api_view(['GET'])
@permission_classes([AllowAny])
def cart_api(request):
    """Return all cart items for the current user/session."""
    cart = get_user_cart(request)
    serializer = CartItemSerializer(cart.items.all(), many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart_api(request):
    """Add a product to the cart (API version)."""
    cart = get_user_cart(request)
    product_id = request.data.get("item_id")
    quantity = int(request.data.get("quantity", 1))

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity = min(item.quantity + quantity, product.stock)
    else:
        item.quantity = min(quantity, product.stock)
    item.save()

    serializer = CartItemSerializer(cart.items.all(), many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_cart_api(request):
    """Update quantity of an item in the cart (API version)."""
    cart = get_user_cart(request)
    cart_item_id = request.data.get("item_id")  # now using CartItem id
    quantity = int(request.data.get("quantity", 1))

    try:
        item = cart.items.get(id=cart_item_id)  # fetch by CartItem ID
    except CartItem.DoesNotExist:
        return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

    if quantity > item.product.stock:
        return Response({"error": "Not enough stock"}, status=status.HTTP_400_BAD_REQUEST)

    item.quantity = max(1, quantity)
    item.save()

    serializer = CartItemSerializer(cart.items.all(), many=True)
    return Response({"cart": serializer.data})  # wrap in "cart" key for JS


@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_from_cart_api(request, item_id):
    """Remove a cart item by its ID."""
    cart = get_user_cart(request)
    try:
        item = cart.items.get(id=item_id)
        item.delete()
    except CartItem.DoesNotExist:
        pass

    serializer = CartItemSerializer(cart.items.all(), many=True)
    return Response({"cart": serializer.data})  # wrap in "cart" key

# ==========================
# 🔹 TEMPLATE (SECURE) VIEW
# ==========================

@require_POST
@csrf_protect
def add_to_cart(request, product_id):
    """
    Secure version for normal website forms (POST only, CSRF-protected).
    Can be called from a template form:
      <form method="POST" action="{% url 'add_to_cart' product.id %}">
          {% csrf_token %}
          <button type="submit">Add to Cart</button>
      </form>
    """
    cart = get_user_cart(request)
    product = get_object_or_404(Product, id=product_id)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity = min(item.quantity + 1, product.stock)
    else:
        item.quantity = 1
    item.save()

    # Redirect back to main page (adjust name as needed)
    return redirect('products_page')
