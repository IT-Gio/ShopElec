import json
import stripe
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from decimal import Decimal
from django.utils import timezone
from django.contrib import messages
from .models import Coupon
from products.models import Product
from .models import Order, OrderItem, Review

stripe.api_key = settings.STRIPE_SECRET_KEY


def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('discount_code', '').strip().lower()
        now = timezone.localtime(timezone.now())  # use local timezone
        print("Now:", now)  # DEBUG

        try:
            coupon = Coupon.objects.get(code__iexact=code)
            print("Coupon found:", coupon.code, coupon.valid_from, coupon.valid_to, coupon.active)  # DEBUG

            # Normalize times for comparison
            valid_from = timezone.localtime(coupon.valid_from)
            valid_to = timezone.localtime(coupon.valid_to)

            if coupon.active and valid_from <= now <= valid_to:
                request.session['coupon_id'] = coupon.id
                messages.success(request, f"Coupon '{coupon.code}' applied! ({coupon.discount}% off)")
                print("✅ Coupon applied:", coupon.code)
            else:
                request.session['coupon_id'] = None
                messages.error(request, "Coupon is not active or expired.")
                print("❌ Coupon expired or inactive.")
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, "Invalid coupon code.")
            print("❌ Coupon not found:", code)

    return redirect('cart')  # adjust if your cart URL name is different


# ---------------- PRODUCT VIEW ----------------
def view_more(request, product_id):
    # Get the main product with average rating
    product = get_object_or_404(
        Product.objects.annotate(avg_rating=Avg("order_reviews__rating")),
        id=product_id
    )

    # Filter similar products by subcategory, exclude current product, with avg_rating
    if product.subcategory:
        similar_products = (
            Product.objects.filter(subcategory=product.subcategory)
            .exclude(id=product.id)
            .annotate(avg_rating=Avg("order_reviews__rating"))[:10]
        )
    else:
        similar_products = Product.objects.none()

    # Check if user purchased the product
    purchased_order_id = None
    if request.user.is_authenticated:
        purchased_orders = Order.objects.filter(
            user=request.user,
            status="completed",
            items__name=product.name
        )
        if purchased_orders.exists():
            purchased_order_id = purchased_orders.first().id

    context = {
        "product": product,
        "similar_products": similar_products,
        "purchased_order_id": purchased_order_id,
    }
    return render(request, "orders/view_more.html", context)


# ---------------- REVIEWS ----------------
@csrf_exempt
def add_review(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=403)

    try:
        data = json.loads(request.body)
        order_id = data.get("order_id")
        product_id = data.get("product_id")
        rating = int(data.get("rating", 0))
        comment = data.get("comment", "")

        if not (order_id and product_id and rating):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        if not 1 <= rating <= 10:
            return JsonResponse({"error": "Rating must be between 1 and 10"}, status=400)

        order = Order.objects.get(id=order_id, user=request.user, status="completed")
        product = Product.objects.get(id=product_id)

        if not order.items.filter(name=product.name).exists():
            return JsonResponse({"error": "Product not in order"}, status=400)

        if Review.objects.filter(user=request.user, product=product, order=order).exists():
            return JsonResponse({"error": "Review already exists"}, status=400)

        review = Review.objects.create(
            user=request.user, product=product, order=order, rating=rating, comment=comment
        )
        return JsonResponse({"success": True, "review_id": review.id})

    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found or not completed"}, status=404)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def add_order_review(request, product_id, order_id):
    product = get_object_or_404(Product, id=product_id)
    order = get_object_or_404(Order, id=order_id, user=request.user, status="completed")

    if request.method == "POST":
        try:
            rating = int(request.POST.get("rating"))
        except (TypeError, ValueError):
            rating = 0

        comment = request.POST.get("comment", "").strip()

        # Validate rating
        if not 1 <= rating <= 10:
            # Optionally, add a message to display in template
            return redirect("orders:view_more", product_id=product.id)

        # Either create a new review or update existing
        review, created = Review.objects.get_or_create(
            user=request.user,
            product=product,
            order=order,
            defaults={"rating": rating, "comment": comment}
        )

        if not created:
            review.rating = rating
            review.comment = comment
            review.save()

    # Redirect back to product page
    return redirect("orders:view_more", product_id=product.id)


# ---------------- STRIPE PAYMENT ----------------
@csrf_exempt
def create_payment_intent(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
        cart = data.get("cart", [])
        if not cart:
            return JsonResponse({"error": "Empty cart"}, status=400)

        # -----------------------------------
        # 1️⃣ Calculate total WITHOUT coupon
        amount = sum(
            Decimal(str(item["price"])) * Decimal(str(item["quantity"]))
            for item in cart
        )

        # 2️⃣ Apply coupon
        coupon_id = request.session.get("coupon_id")
        discount_amount = Decimal("0")

        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                discount_amount = (amount * coupon.discount / Decimal("100"))
                print(f"Coupon {coupon.code} applied: -{discount_amount}")
            except Coupon.DoesNotExist:
                pass
            
        # 3️⃣ Apply shipping fee
        shipping_fee = Decimal("0")
        subtotal_after_discount = amount - discount_amount

        if subtotal_after_discount < 0:
            subtotal_after_discount = Decimal("0")

        if subtotal_after_discount < Decimal("300"):
            shipping_fee = subtotal_after_discount * Decimal("0.10")  # 10%
        else:
            shipping_fee = Decimal("0")

        final_total = subtotal_after_discount + shipping_fee

        # Prevent negative values
        if final_total < 0:
            final_total = Decimal("0.00")

        # If total is zero → free order
        if final_total <= 0:
            return JsonResponse({
                "freeOrder": True,
                "subtotal": float(amount),
                "discount": float(discount_amount),
                "shipping_fee": float(shipping_fee),
                "final_total": 0,
            })

        amount_cents = int(final_total * 100)

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
        )

        return JsonResponse({
            "clientSecret": intent.client_secret,
            "subtotal": float(amount),
            "discount": float(discount_amount),
            "shipping_fee": float(shipping_fee),
            "final_total": float(final_total),
        })


    except Exception as e:
        print("❌ create_payment_intent error:", e)
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def complete_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
        cart = data.get("cart", [])
        address = data.get("address", "")
        payment_intent_id = data.get("paymentIntentId", "")
        email = data.get("email", "").strip()

        # If user is logged in, prefer their email
        if request.user.is_authenticated and request.user.email:
            email = request.user.email

        # Basic validation
        if not cart or not email or not payment_intent_id:
            return JsonResponse({"error": "Missing data"}, status=400)

        # 1️⃣ Subtotal
        total_price = sum(
            Decimal(str(i.get("price", 0))) * Decimal(str(i.get("quantity", 1)))
            for i in cart
        )
        
        # 2️⃣ Discount
        discount = Decimal(0)
        coupon = None
        coupon_id = request.session.get("coupon_id")
        
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                if coupon.is_valid():
                    discount = (coupon.discount / Decimal(100)) * total_price
            except Coupon.DoesNotExist:
                pass
            
        subtotal_after_discount = total_price - discount
        if subtotal_after_discount < 0:
            subtotal_after_discount = Decimal("0")
        
        # 3️⃣ Shipping
        if subtotal_after_discount >= Decimal("300"):
            shipping_fee = Decimal("0")
        else:
            shipping_fee = subtotal_after_discount * Decimal("0.10")
        
        # 4️⃣ Final total
        final_price = subtotal_after_discount + shipping_fee
        

        # 4️⃣ Create the order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=email,
            address=address,
            total_price=final_price,
            payment_intent_id=payment_intent_id,
            status="completed",
        )

        # Save coupon info on the order if used
        if coupon:
            order.coupon = coupon
            order.discount_amount = discount
            order.save()

        # 5️⃣ Create order items
        for item in cart:
            product = Product.objects.filter(name=item.get("name")).first()
            OrderItem.objects.create(
                order=order,
                product=product,
                name=item.get("name", ""),
                brand=item.get("brand", ""),
                category=item.get("category", ""),
                price=item.get("price", 0),
                quantity=item.get("quantity", 1),
            )

        # 6️⃣ Send confirmation email
        order_lines = "\n".join([
            f'{i["quantity"]}x {i["name"]} - ${i["price"]}' for i in cart
        ])
        message = (
            f"Thank you for your order!\n\n"
            f"Delivery address: {address}\n\n"
            f"Items:\n{order_lines}\n\n"
            f"Subtotal: ${total_price:.2f}\n"
            f"Discount: -${discount:.2f}\n"
            f"Total Paid: ${final_price:.2f}\n\n"
            f"We appreciate your purchase!"
        )
        send_mail(
            subject="Your Order Confirmation",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        # 7️⃣ Try clearing user's cart
        try:
            from shop.utils import get_user_cart
            cart_obj = get_user_cart(request)
            cart_obj.items.all().delete()
        except Exception as e:
            print("Cart clearing failed:", e)

        # 8️⃣ Clear applied coupon after checkout
        request.session["coupon_id"] = None

        order_item_ids = [item.id for item in order.items.all()]
        return JsonResponse({
            "success": True,
            "order_id": order.id,
            "order_item_ids": order_item_ids,
            "discount": float(discount),
            "total_paid": float(final_price),
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ---------------- OPTIONAL LEGACY SAVE ORDER ----------------
@csrf_exempt
def save_order(request, product_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=403)

    product = get_object_or_404(Product, id=product_id)
    data = json.loads(request.body)
    payment_intent_id = data.get("paymentIntentId", "")
    if not payment_intent_id:
        return JsonResponse({"error": "Missing paymentIntentId"}, status=400)

    order = Order.objects.create(
        user=request.user,
        email=request.user.email,
        total_price=product.price or 0,
        payment_intent_id=payment_intent_id,
        status="completed"
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        name=product.name,
        brand=product.brand or "",
        category=product.category or "",
        price=product.price or 0,
        quantity=1
    )
    return JsonResponse({"success": True, "order_id": order.id})
