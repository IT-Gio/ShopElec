from django.urls import path
from .views import products_page, ProductList, ProductDetail, cart_view, category_list
from . import views
urlpatterns = [
    # Template views
    path('', products_page, name='home'),                # /
    path('products/', products_page, name='products-page'),  # /products/

    # API views
    path('api/products/', ProductList.as_view(), name='product-list'),
    path('api/products/<int:pk>/', ProductDetail.as_view(), name='product-detail'),

    # Categories
    path("api/categories/", category_list, name="category-list"),

    # Cart
    path('cart/', cart_view, name='cart'),

    #view more
    path('product/<int:pk>/', views.view_more, name='view_more'),

]
