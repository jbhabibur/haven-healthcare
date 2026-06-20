from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Cart URLs (Placed at the top to prevent routing conflicts)
    path('cart/add/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart_view, name='remove_from_cart'),

    # Product details page route
    path('medicine/<slug:slug>/', views.medicine_detail, name='medicine_detail'), 
    
    # Category-wise product list page (Class-based View)
    path('<slug:category_slug>/', views.CategoryProductListView.as_view(), name='category_products'),
]