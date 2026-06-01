from .cart import Cart

def cart(request):
    cart_instance = Cart(request)
    return {
        'cart': cart_instance,
        'cart_count': len(cart_instance)
    }
