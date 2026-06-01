from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from products.models import Product
from accounts.models import Address, Notification
from .cart import Cart
from .models import Order, OrderItem, Coupon

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override', 'False') == 'True'
    
    selected_size = request.POST.get('size_variant', 'Standard')
    selected_color = request.POST.get('color_variant', 'Default Slate')
    
    if product.stock < quantity and not override:
        messages.error(request, f"Sorry, only {product.stock} items left in stock for {product.name}.")
        return redirect('product_detail', slug=product.slug)
    
    cart.add(
        product=product, 
        quantity=quantity, 
        override_quantity=override,
        selected_size=selected_size,
        selected_color=selected_color
    )
    messages.success(request, f"{product.name} added to cart.")
    return redirect('cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f"{product.name} removed from cart.")
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart.html', {'cart': cart})

@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty. Please add items to checkout.")
        return redirect('catalog')

    # Load customer addresses
    addresses = request.user.addresses.all()

    # Calculate discount from coupon
    coupon_id = request.session.get('coupon_id')
    coupon = None
    discount = Decimal('0.00')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            discount = cart.get_total_price() * (Decimal(coupon.discount_percent) / Decimal('100'))
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None

    subtotal = cart.get_total_price()
    total_price = subtotal - discount

    if request.method == 'POST':
        # Check if saved address is selected
        address_id = request.POST.get('saved_address')
        if address_id and address_id != 'new':
            address_obj = get_object_or_404(Address, id=address_id, user=request.user)
            first_name = address_obj.first_name
            last_name = address_obj.last_name
            email = request.user.email
            address = address_obj.address_line1
            if address_obj.address_line2:
                address += f", {address_obj.address_line2}"
            city = address_obj.city
            postal_code = address_obj.postal_code
            country = address_obj.country
        else:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            address = request.POST.get('address')
            city = request.POST.get('city')
            postal_code = request.POST.get('postal_code')
            country = request.POST.get('country', 'United States')

        if not all([first_name, last_name, email, address, city, postal_code]):
            messages.error(request, "Please fill in all the required checkout fields.")
            return render(request, 'checkout.html', {
                'cart': cart, 
                'addresses': addresses,
                'coupon': coupon,
                'discount': discount,
                'total_price': total_price
            })

        # Validate stock for all items
        for item in cart:
            product = item['product']
            if product.stock < item['quantity']:
                messages.error(request, f"Insufficient stock for {product.name}. Only {product.stock} available.")
                return redirect('cart_detail')

        # Create Order
        order = Order.objects.create(
            customer=request.user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            city=city,
            postal_code=postal_code,
            country=country,
            total_amount=total_price,
            status='PAID'
        )

        # Create Order Items and update vendor profiles / product stocks
        for item in cart:
            product = item['product']
            item_cost = item['price'] * item['quantity']
            
            OrderItem.objects.create(
                order=order,
                product=product,
                vendor=product.vendor,
                price=item['price'],
                quantity=item['quantity'],
                selected_size=item.get('selected_size', 'Standard'),
                selected_color=item.get('selected_color', 'Default Slate'),
                status='PENDING'
            )
            
            # Reduce product stock
            product.stock -= item['quantity']
            product.save()

            # Credit Vendor's account balance (90% to vendor)
            vendor_share = item_cost * Decimal('0.90')
            product.vendor.balance += vendor_share
            product.vendor.save()

            # Send Notification to Vendor
            Notification.objects.create(
                user=product.vendor.user,
                title="New Order Received",
                message=f"Storefront sold {item['quantity']}x of '{product.name}' for a total credit of ${vendor_share:.2f}."
            )

        # Clear cart and coupon from session
        cart.clear()
        request.session['coupon_id'] = None
        
        # Send Notification to Buyer
        Notification.objects.create(
            user=request.user,
            title="Order Placed Successfully",
            message=f"Thank you for your purchase! Order #{order.id} for a total of ${total_price:.2f} has been created and confirmed."
        )

        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {
        'cart': cart,
        'addresses': addresses,
        'coupon': coupon,
        'discount': discount,
        'total_price': total_price
    })

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip()
        try:
            coupon = Coupon.objects.get(code__iexact=code, active=True)
            request.session['coupon_id'] = coupon.id
            messages.success(request, f"Coupon '{code}' applied! You save {coupon.discount_percent}% on this order.")
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, f"Invalid or expired coupon code '{code}'.")
    return redirect('checkout')

@login_required
def remove_coupon(request):
    request.session['coupon_id'] = None
    messages.info(request, "Coupon removed.")
    return redirect('checkout')

def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'order_success.html', {'order': order})

@login_required
@require_POST
def order_item_refund(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__customer=request.user)
    
    if order_item.status not in ['DELIVERED', 'SHIPPED']:
        messages.error(request, "You can only request refunds for shipped or delivered items.")
        return redirect('/dashboard/customer/?tab=orders')
        
    if order_item.status == 'REFUND_REQUESTED':
        messages.warning(request, "Refund request has already been filed for this item.")
        return redirect('/dashboard/customer/?tab=orders')
        
    order_item.status = 'REFUND_REQUESTED'
    order_item.save()
    
    # Notify Vendor
    Notification.objects.create(
        user=order_item.vendor.user,
        title="Refund Requested by Customer",
        message=f"A buyer requested a refund for '{order_item.product.name}' in Order #{order_item.order.id}. Please review this in your merchant fulfills queue."
    )
    
    # Notify Buyer
    Notification.objects.create(
        user=request.user,
        title="Refund Request Submitted",
        message=f"Your refund request for '{order_item.product.name}' (Order #{order_item.order.id}) has been submitted and is pending merchant review."
    )
    
    messages.success(request, f"Refund request for '{order_item.product.name}' has been successfully filed.")
    return redirect('/dashboard/customer/?tab=orders')
