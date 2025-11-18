# shop/serializers.py
from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer  # optional, if you want product details
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    # Flattened product fields
    name = serializers.CharField(source="product.name", read_only=True)
    description = serializers.CharField(source="product.description", read_only=True)
    brand = serializers.CharField(source="product.brand", read_only=True)
    category = serializers.CharField(source="product.category", read_only=True)
    subcategory = serializers.CharField(source="product.subcategory", read_only=True)
    image = serializers.ImageField(source="product.image", read_only=True)
    price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)
    average_rating = serializers.FloatField(source="product.average_rating", read_only=True)

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",  # keep reference to product object (optional)
            "name",
            "description",
            "brand",
            "category",
            "subcategory",
            "image",
            "price",
            "quantity",
            "total_price",
            "average_rating",
        ]

    def get_total_price(self, obj):
        try:
            return float(obj.product.price) * obj.quantity
        except Exception:
            return 0

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.FloatField(source='total_price', read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'session_key', 'items', 'total_price']
