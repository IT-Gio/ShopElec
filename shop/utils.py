
from .models import Cart, CartItem

def get_user_cart(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    # Remove duplicates automatically
    carts = Cart.objects.filter(session_key=session_key)
    if carts.count() > 1:
        cart = carts.first()
        carts.exclude(id=cart.id).delete()
    elif carts.exists():
        cart = carts.first()
    else:
        cart = Cart.objects.create(session_key=session_key)

    return cart
