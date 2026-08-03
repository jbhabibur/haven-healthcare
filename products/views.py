from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.db.models import Avg, Q
from django.http import JsonResponse
import json
from .models import MedicineCategory, MedicineProduct, MedicineReview

# Category-wise & Search-enabled Medicine Product List View
class CategoryProductListView(ListView):
    model = MedicineProduct
    template_name = 'products/collection.html' 
    context_object_name = 'products'
    paginate_by = 12  

    def get_queryset(self):
        slug = self.kwargs['category_slug']
        
        # Base queryset with database optimizations
        queryset = MedicineProduct.objects.filter(is_available=True).select_related('manufacturer', 'generic_name')
        
        # Filter by Category setup
        if slug == 'shop':
            # Create a mock/fake category object for the template
            self.category = {'name': 'All Medicines', 'slug': 'shop'}
        else:
            # Fetch the actual category from DB
            self.category = get_object_or_404(MedicineCategory, slug=slug, is_active=True)
            queryset = queryset.filter(category=self.category)

        # Extract and evaluate search keywords safely from request URL parameters
        search_query = self.request.GET.get('q')
        if search_query:
            search_query = search_query.strip()
            # Perform multi-field lookup across related foreign tables using OR logic gates
            queryset = queryset.filter(
                Q(name__icontains=search_query) |                         # Brand name
                Q(generic_name__name__icontains=search_query) |           # Chemical formulation name
                Q(manufacturer__name__icontains=search_query) |           # Manufacturing company name
                Q(strength__icontains=search_query)                       # Dosage metrics (e.g., 500mg)
            ).distinct()                                                  # Eliminate row duplicates caused by structural joins
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        
        # Pass current search query string back to template engine to hold state inside navigation layout text boxes
        context['search_query'] = self.request.GET.get('q', '').strip()
        
        # Calculate top-rated medicines dynamically using your MedicineReview model
        context['top_rated_products'] = MedicineProduct.objects.filter(is_available=True) \
            .annotate(avg_rating=Avg('reviews__rating')) \
            .order_by('-avg_rating')[:5]
            
        return context


# Medicine Details Page View
def medicine_detail(request, slug):
    # Fetching product along with manufacturer, category, and generic name in a single query
    product = get_object_or_404(
        MedicineProduct.objects.select_related('category', 'generic_name', 'manufacturer'), 
        slug=slug,
        is_available=True
    )
    
    # Prefetching related tab data
    images = product.images.all()
    faqs = product.faqs.all()
    # Only pull reviews that are approved by moderation
    reviews = product.reviews.filter(is_approved=True)
    
    # Calculate average rating for this specific product
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'product': product,
        'images': images,
        'faqs': faqs,
        'reviews': reviews,
        'average_rating': round(average_rating, 1),
    }
    
    return render(request, 'products/product_detail.html', context)


# Ajax View to Add Product into Session Cart (Newly Added)
def add_to_cart_view(request):
    if request.method == 'POST':
        try:
            # Load JSON data sent from Alpine.js template
            data = json.loads(request.body)
            product_id = str(data.get('id'))
            quantity = int(data.get('quantity', 1))
            
            # Fetch the medicine product safely
            product = get_object_or_404(MedicineProduct, id=product_id, is_available=True)
            
            # Validate requesting quantity against available stock limits
            if product.stock_quantity < quantity:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Not enough stock available! Maximum limit: {product.stock_quantity}'
                }, status=400)

            # Access or initialize the native session storage
            cart = request.session.get('cart', {})
            
            # Evaluate quantity modifications mapping to product id keys
            if product_id in cart:
                new_qty = cart[product_id] + quantity
                if new_qty > product.stock_quantity:
                    return JsonResponse({
                        'status': 'error', 
                        'message': f'Cannot add more items. Only {product.stock_quantity} left in stock.'
                    }, status=400)
                cart[product_id] = new_qty
            else:
                cart[product_id] = quantity
                
            # Commit mutations back to the session context
            request.session['cart'] = cart
            request.session.modified = True 
            
            # Calculate aggregate items count
            total_items = sum(cart.values())
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Product successfully added to cart!',
                'total_items': total_items
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


# Cart Page View (Newly Added)
def cart_detail_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = 0
    
    if cart:
        # Fetching products present inside the session cart dictionary keys
        product_ids = cart.keys()
        products = MedicineProduct.objects.filter(id__in=product_ids, is_available=True).select_related('manufacturer')
        
        for product in products:
            quantity = cart[str(product.id)]
            total_price = product.selling_price * quantity
            subtotal += total_price
            
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': total_price,
            })
            
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_charge': 60 if subtotal > 0 else 0,  # Demo Delivery Charge
        'total': subtotal + (60 if subtotal > 0 else 0)
    }
    return render(request, 'products/cart.html', context)


# Remove Item from Cart View (Newly Added)
def remove_from_cart_view(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            del cart[product_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            
    return redirect('products:cart_detail')