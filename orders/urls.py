from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [

    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('complete/', views.complete_order, name='complete_order'),
    
    # Payment and order management
    path("create-payment-intent/", views.create_payment_intent, name="create_payment_intent"),
    path("save-order/<int:product_id>/", views.save_order, name="save_order"),
    path("complete-order/", views.complete_order, name="complete_order"),

    # Reviews
    path("add-review/", views.add_review, name="add_review"),
    path(
        "product/<int:product_id>/review/<int:order_id>/",
        views.add_order_review,
        name="add_order_review",
    ),

    # Product details (used for redirect)
    path(
        "product/<int:product_id>/",
        views.view_more,
        name="view_more",
    ),
]
