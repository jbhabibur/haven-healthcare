from django.shortcuts import render
from django.db.models import Avg
from products.models import MedicineProduct

def home_view(request):
    # Fetching first 8 available products
    products = MedicineProduct.objects.filter(is_available=True).select_related('manufacturer', 'generic_name')[:8]
    
    # Fetching top 5 rated products dynamic context data
    top_rated_products = MedicineProduct.objects.filter(is_available=True) \
        .annotate(avg_rating=Avg('reviews__rating')) \
        .order_by('-avg_rating')[:5]
        
    context = {
        'products': products,
        'top_rated_products': top_rated_products,
        'category': {'name': 'Unani & Natural Products', 'slug': 'shop'},
    }
    return render(request, 'includes/home.html', context)