from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Count, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from .models import Category, Product, Review
from accounts.models import VendorProfile

def catalog(request):
    categories = Category.objects.all().order_by('name')
    products = Product.objects.filter(is_active=True).select_related('vendor', 'category')
    
    # Search query
    search_query = (request.GET.get('search') or '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(vendor__store_name__icontains=search_query)
        )

    # Filter by category
    category_slug = (request.GET.get('category') or '').strip()
    active_category = None
    if category_slug:
        active_category = Category.objects.filter(slug=category_slug).first()
        products = products.filter(category=active_category) if active_category else products.none()
        
    # Filter by vendor
    vendor_id = (request.GET.get('vendor') or '').strip()
    active_vendor = None
    if vendor_id:
        try:
            active_vendor = int(vendor_id)
            products = products.filter(vendor_id=active_vendor)
        except (TypeError, ValueError):
            products = products.none()
        
    # Filter by price range
    min_price = (request.GET.get('min_price') or '').strip()
    max_price = (request.GET.get('max_price') or '').strip()
    try:
        if min_price:
            products = products.filter(price__gte=Decimal(min_price))
    except (InvalidOperation, ValueError):
        min_price = ''
    try:
        if max_price:
            products = products.filter(price__lte=Decimal(max_price))
    except (InvalidOperation, ValueError):
        max_price = ''
        
    # Filter by rating (annotate average rating)
    products = products.annotate(avg_rating=Coalesce(Avg('reviews__rating'), Value(0.0)))
    
    min_rating = (request.GET.get('rating') or '').strip()
    try:
        if min_rating:
            rating_value = Decimal(min_rating)
            if Decimal('1') <= rating_value <= Decimal('5'):
                products = products.filter(avg_rating__gte=rating_value)
            else:
                min_rating = ''
    except (InvalidOperation, ValueError):
        min_rating = ''
        
    # Filter by availability
    in_stock = request.GET.get('in_stock')
    if in_stock == 'true':
        products = products.filter(stock__gt=0)
        
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-avg_rating')
    else:  # newest
        products = products.order_by('-created_at')

    is_partial_request = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('partial') == 'true'
    has_extra_filters = any([category_slug, vendor_id, min_price, max_price, min_rating, in_stock == 'true'])
    if search_query and not has_extra_filters and not is_partial_request:
        exact_product = products.filter(name__iexact=search_query).first()
        if exact_product:
            return redirect('product_detail', slug=exact_product.slug)
        if products.count() == 1:
            return redirect('product_detail', slug=products.first().slug)

    # Fetch unique vendors for the filter sidebar
    vendors = VendorProfile.objects.filter(status='APPROVED').order_by('store_name')

    context = {
        'categories': categories,
        'products': products,
        'vendors': vendors,
        'active_category': active_category,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'min_rating': min_rating,
        'in_stock': in_stock,
        'sort_by': sort_by,
        'active_vendor': active_vendor,
    }
    
    # Check if AJAX partial page request
    if is_partial_request:
        return render(request, 'partials/product_grid.html', context)
        
    return render(request, 'landing.html', context)

def privacy_policy(request):
    return render(request, 'privacy.html')

def terms_page(request):
    return render(request, 'terms.html')

def product_detail(request, slug):
    product = get_object_or_404(Product.objects.annotate(avg_rating=Avg('reviews__rating')), slug=slug, is_active=True)
    reviews = product.reviews.all().select_related('user')
    
    # Calculate stars distribution
    stars_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        stars_count[r.rating] = stars_count.get(r.rating, 0) + 1
        
    reviews_count = reviews.count()
    stars_pct = {}
    for i in range(1, 6):
        stars_pct[i] = int((stars_count[i] / reviews_count * 100)) if reviews_count > 0 else 0
        
    # Get related products (same category, excluding current product, limit to 4)
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id).annotate(avg_rating=Avg('reviews__rating'))[:4]
    
    # Track recently viewed in session
    recently_viewed_ids = request.session.get('recently_viewed', [])
    if product.id in recently_viewed_ids:
        recently_viewed_ids.remove(product.id)
    recently_viewed_ids.insert(0, product.id)
    recently_viewed_ids = recently_viewed_ids[:5]
    request.session['recently_viewed'] = recently_viewed_ids
    
    # Fetch recently viewed products (excluding current one)
    recently_viewed = Product.objects.filter(id__in=recently_viewed_ids).exclude(id=product.id).annotate(avg_rating=Avg('reviews__rating'))[:4]
    
    # Check if current user has already reviewed
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    context = {
        'product': product,
        'reviews': reviews,
        'reviews_count': reviews_count,
        'stars_pct': stars_pct,
        'stars_count': stars_count,
        'related_products': related_products,
        'recently_viewed': recently_viewed,
        'user_review': user_review,
    }
    return render(request, 'product_detail.html', context)

def search_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []
    if len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query),
            is_active=True
        ).select_related('category')[:6]
        
        suggestions = [{
            'name': p.name,
            'slug': p.slug,
            'price': str(p.price),
            'image_url': p.image_url,
            'category': p.category.name
        } for p in products]
        
    return JsonResponse({'suggestions': suggestions})

@login_required
@require_POST
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '')
    
    if rating < 1 or rating > 5:
        messages.error(request, "Rating must be between 1 and 5.")
        return redirect('product_detail', slug=product.slug)
        
    review, created = Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={'rating': rating, 'comment': comment}
    )
    
    messages.success(request, "Your review has been saved!" if created else "Your review has been updated.")
    return redirect('product_detail', slug=product.slug)
