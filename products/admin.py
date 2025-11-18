from django.contrib import admin
from .models import Product, Brand, Category, SubCategory

admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product)
