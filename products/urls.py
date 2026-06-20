from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product details page route
    path('medicine/<slug:slug>/', views.medicine_detail, name='medicine_detail'), 
    
    # Category-wise product list page (Class-based View)
    path('<slug:category_slug>/', views.CategoryProductListView.as_view(), name='category_products'),
    
    
]