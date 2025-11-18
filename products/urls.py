# products/urls.py
from django.urls import path
from .views import home, products_page, ProductList, ProductDetail, cart_view, category_list
from shop.views import cart_api, add_to_cart_api, update_cart_api, remove_from_cart_api, add_to_cart

urlpatterns = [
    # ---------------- TEMPLATE VIEWS ----------------                   # /
    path('', home, name='home'),
    path('products/', products_page, name='products-page'),   # /products/
    path('cart/', cart_view, name='cart'),                    # template page

    # ---------------- TEMPLATE: Add to Cart (Secure) ----------------
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),

    # ---------------- API: Products ----------------
    path('api/products/', ProductList.as_view(), name='product-list'),
    path('api/products/<int:pk>/', ProductDetail.as_view(), name='product-detail'),

    # ---------------- API: Categories ----------------
    path("api/categories/", category_list, name="category-list"),

    # ---------------- API: Cart ----------------
    path('api/cart/', cart_api, name='cart-api'),                        # GET: get cart items
    path('api/cart/add/', add_to_cart_api, name='add-to-cart-api'),      # POST: add item
    path('api/cart/update/', update_cart_api, name='update-cart-api'),   # POST: update quantity
    path('api/cart/remove/<int:item_id>/', remove_from_cart_api, name='remove-from-cart-api'),

]
