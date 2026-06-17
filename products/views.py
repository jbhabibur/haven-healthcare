from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.db.models import Avg
from .models import MedicineCategory, MedicineProduct, MedicineReview

# Category-wise Medicine Product List View
class CategoryProductListView(ListView):
    model = MedicineProduct
    template_name = 'products/collection.html' 
    context_object_name = 'products'
    paginate_by = 12  

    def get_queryset(self):
        slug = self.kwargs['category_slug']
        
        # Base queryset with optimizations
        queryset = MedicineProduct.objects.filter(is_available=True).select_related('manufacturer', 'generic_name')
        
        if slug == 'shop':
            # Create a mock/fake category object for the template
            self.category = {'name': 'All Medicines', 'slug': 'shop'}
            return queryset
        else:
            # Fetch the actual category from DB
            self.category = get_object_or_404(MedicineCategory, slug=slug, is_active=True)
            return queryset.filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        
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