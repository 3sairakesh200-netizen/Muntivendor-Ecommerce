from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from .models import User, VendorProfile, Address, Wishlist, Notification
from products.models import Product

def login_view(request):
    if request.user.is_authenticated:
        return redirect('catalog')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('catalog')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('catalog')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('catalog')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'register.html')
            
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_customer=True,
            is_vendor=False
        )
        # Create a welcome notification
        Notification.objects.create(
            user=user,
            title="Welcome to Lumio!",
            message="Your account is active. Explore our high-tech artisan catalog, create wishlists, and manage your delivery details from your dashboard."
        )
        login(request, user)
        messages.success(request, "Registration successful! Welcome to Lumio.")
        return redirect('catalog')
        
    return render(request, 'register.html')

def vendor_register_view(request):
    if request.user.is_authenticated and hasattr(request.user, 'vendor_profile'):
        return redirect('dashboard_home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        store_name = request.POST.get('store_name')
        description = request.POST.get('description', '')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'vendor_register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'vendor_register.html')
            
        if VendorProfile.objects.filter(store_name=store_name).exists():
            messages.error(request, "Store name is already taken.")
            return render(request, 'vendor_register.html')
            
        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_customer=False,
            is_vendor=True
        )
        
        # Create Vendor Profile (Auto-Approved for demo/usability)
        VendorProfile.objects.create(
            user=user,
            store_name=store_name,
            description=description,
            status='APPROVED' 
        )
        
        # Welcome notification
        Notification.objects.create(
            user=user,
            title="Merchant Portal Setup Complete",
            message=f"Welcome to the storefront: {store_name}. You can now start listing products and monitoring metrics on your Vendor Dashboard."
        )
        
        login(request, user)
        messages.success(request, f"Vendor registration successful! Welcome to your storefront: {store_name}.")
        return redirect('dashboard_home')
        
    return render(request, 'vendor_register.html')

# Customer Dashboard & Details Views
@login_required
def customer_dashboard(request):
    active_tab = request.GET.get('tab', 'orders')
    orders = request.user.orders.all().prefetch_related('items__product').order_by('-created_at')
    addresses = request.user.addresses.all().order_by('-is_default', '-id')
    wishlist = request.user.wishlist_items.all().select_related('product')
    notifications = request.user.notifications.all().order_by('-created_at')

    context = {
        'active_tab': active_tab,
        'orders': orders,
        'addresses': addresses,
        'wishlist': wishlist,
        'notifications': notifications,
    }
    return render(request, 'dashboard_customer.html', context)

@login_required
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product)
    
    if wishlist_item.exists():
        wishlist_item.delete()
        added = False
        messages.success(request, f"Removed {product.name} from your wishlist.")
    else:
        Wishlist.objects.create(user=request.user, product=product)
        added = True
        messages.success(request, f"Added {product.name} to your wishlist.")
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'added': added, 'wishlist_count': request.user.wishlist_items.count()})
        
    return redirect(request.META.get('HTTP_REFERER', 'catalog'))

@login_required
def address_create(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2', '')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country', 'United States')
        is_default = request.POST.get('is_default') == 'on'
        
        if not all([first_name, last_name, address_line1, city, state, postal_code]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('/dashboard/customer/?tab=addresses')
            
        # Force default if it's the first address
        if not request.user.addresses.exists():
            is_default = True
            
        Address.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default
        )
        messages.success(request, "Address added successfully.")
        
    return redirect('/dashboard/customer/?tab=addresses')

@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    was_default = address.is_default
    address.delete()
    
    if was_default:
        next_address = request.user.addresses.first()
        if next_address:
            next_address.is_default = True
            next_address.save()
            
    messages.success(request, "Address deleted successfully.")
    return redirect('/dashboard/customer/?tab=addresses')

@login_required
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, "Default address updated.")
    return redirect('/dashboard/customer/?tab=addresses')

@login_required
@require_POST
def profile_update(request):
    user = request.user
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    email = request.POST.get('email', '')
    avatar_url = request.POST.get('avatar_url', '')
    
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    if avatar_url:
        user.avatar_url = avatar_url
    user.save()
    
    messages.success(request, "Profile updated successfully.")
    return redirect('/dashboard/customer/?tab=settings')

@login_required
def notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})
