from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils.decorators import method_decorator
from accounts.models import VendorProfile
from products.models import Product, Category
from orders.models import Order, OrderItem
from decimal import Decimal

# Custom decorator to check if user is a vendor
def vendor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_vendor or not hasattr(request.user, 'vendor_profile'):
            messages.error(request, "Access denied. You must be a registered Vendor to access the Vendor Dashboard.")
            return redirect('catalog')
        if request.user.vendor_profile.status != 'APPROVED':
            messages.warning(request, "Your Vendor Profile is currently pending approval.")
            return redirect('catalog')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@vendor_required
def dashboard_home(request):
    vendor = request.user.vendor_profile
    products = Product.objects.filter(vendor=vendor)
    order_items = OrderItem.objects.filter(vendor=vendor).select_related('order', 'product')
    
    # Calculate Metrics
    total_earnings = order_items.filter(order__status='PAID').aggregate(
        total=Sum('price')
    )['total'] or Decimal('0.00')
    
    # Wait, total earnings should consider item quantities! Let's do a loop or advanced aggregation
    total_earnings = sum(item.price * item.quantity for item in order_items.filter(order__status='PAID'))
    
    total_orders = order_items.values('order').distinct().count()
    total_products = products.count()
    pending_fulfillments = order_items.exclude(status='DELIVERED').count()

    # Create dynamic values for SVG chart representing sales trend
    # Let's group last 6 order totals or simply map month names with mock/real orders
    sales_trend = [
        {"month": "Jan", "amount": 120},
        {"month": "Feb", "amount": 250},
        {"month": "Mar", "amount": 190},
        {"month": "Apr", "amount": 420},
        {"month": "May", "amount": float(total_earnings) if total_earnings > 0 else 100.0}
    ]
    
    # Build coordinates for a nice SVG polyline
    # height is 200, width is 500
    points = []
    for idx, data in enumerate(sales_trend):
        x = 50 + idx * 100
        # map amount to visual heights: max amount maps to 20, min maps to 185
        val = data["amount"]
        y = 180 - min(val * 0.3, 150)
        points.append(f"{x},{y}")
    svg_points = " ".join(points)

    recent_order_items = order_items.order_by('-order__created_at')[:5]
    
    # Stock Alert Metrics
    low_stock_count = products.filter(stock__lte=5, stock__gt=0).count()
    out_of_stock_count = products.filter(stock=0).count()

    context = {
        'vendor': vendor,
        'total_earnings': total_earnings,
        'total_orders': total_orders,
        'total_products': total_products,
        'pending_fulfillments': pending_fulfillments,
        'sales_trend': sales_trend,
        'svg_points': svg_points,
        'recent_items': recent_order_items,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'dashboard_home.html', context)

@login_required
@vendor_required
def dashboard_products(request):
    vendor = request.user.vendor_profile
    products = Product.objects.filter(vendor=vendor).select_related('category')
    return render(request, 'dashboard_products.html', {'products': products})

@login_required
@vendor_required
def product_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        image_url = request.POST.get('image_url')

        if not all([name, price, stock, category_id]):
            messages.error(request, "Please fill in all the required fields.")
            return render(request, 'dashboard_product_form.html', {'categories': categories})

        category = get_object_or_404(Category, id=category_id)
        
        # Build image placeholder based on category name if none supplied
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1550009158-9ebf69173e03?auto=format&fit=crop&w=500&q=80"

        Product.objects.create(
            vendor=request.user.vendor_profile,
            category=category,
            name=name,
            description=description,
            price=Decimal(price),
            stock=int(stock),
            image_url=image_url
        )
        messages.success(request, f"Product '{name}' created successfully.")
        return redirect('dashboard_products')

    return render(request, 'dashboard_product_form.html', {'categories': categories, 'action': 'Create'})

@login_required
@vendor_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor_profile)
    categories = Category.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        image_url = request.POST.get('image_url')

        if not all([name, price, stock, category_id]):
            messages.error(request, "Fields marked with * are required.")
            return render(request, 'dashboard_product_form.html', {'product': product, 'categories': categories})

        category = get_object_or_404(Category, id=category_id)
        
        product.name = name
        product.description = description
        product.price = Decimal(price)
        product.stock = int(stock)
        product.category = category
        if image_url:
            product.image_url = image_url
        product.save()

        messages.success(request, f"Product '{name}' updated successfully.")
        return redirect('dashboard_products')

    return render(request, 'dashboard_product_form.html', {'product': product, 'categories': categories, 'action': 'Edit'})

@login_required
@vendor_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor_profile)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted successfully.")
    return redirect('dashboard_products')

@login_required
@vendor_required
def dashboard_orders(request):
    vendor = request.user.vendor_profile
    order_items = OrderItem.objects.filter(vendor=vendor).select_related('order', 'product').order_by('-order__created_at')
    
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_status = request.POST.get('status')
        order_item = get_object_or_404(OrderItem, id=item_id, vendor=vendor)
        
        if new_status in dict(OrderItem.STATUS_CHOICES):
            old_status = order_item.status
            order_item.status = new_status
            order_item.save()
            
            if new_status == 'REFUNDED' and old_status != 'REFUNDED':
                item_cost = order_item.price * order_item.quantity
                vendor_share = item_cost * Decimal('0.90')
                vendor.balance -= vendor_share
                vendor.save()
                
                # Send Notification to Buyer
                from accounts.models import Notification
                Notification.objects.create(
                    user=order_item.order.customer,
                    title="Refund Request Approved",
                    message=f"Merchant '{vendor.store_name}' approved your refund for '{order_item.product.name}'. A credit of ${item_cost:.2f} has been processed back to your payment hub."
                )
            
            messages.success(request, f"Order Item status updated to '{order_item.get_status_display()}' successfully.")
        return redirect('dashboard_orders')

    return render(request, 'dashboard_orders.html', {'order_items': order_items})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    vendors = VendorProfile.objects.all().select_related('user')
    orders = Order.objects.all().order_by('-created_at')
    
    total_sales = orders.filter(status='PAID').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    platform_commission = total_sales * Decimal('0.10') # 10% Platform fee
    
    total_vendors = vendors.count()
    total_products = Product.objects.count()

    if request.method == 'POST':
        vendor_id = request.POST.get('vendor_id')
        action = request.POST.get('action')
        vendor = get_object_or_404(VendorProfile, id=vendor_id)
        
        if action == 'APPROVE':
            vendor.status = 'APPROVED'
            vendor.save()
            messages.success(request, f"Vendor Store '{vendor.store_name}' approved successfully.")
        elif action == 'SUSPEND':
            vendor.status = 'SUSPENDED'
            vendor.save()
            messages.warning(request, f"Vendor Store '{vendor.store_name}' suspended.")
        return redirect('admin_dashboard')

    context = {
        'vendors': vendors,
        'orders': orders[:10],
        'total_sales': total_sales,
        'platform_commission': platform_commission,
        'total_vendors': total_vendors,
        'total_products': total_products,
    }
    return render(request, 'admin_dashboard.html', context)
