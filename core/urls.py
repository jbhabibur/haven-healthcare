from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from .views import home_view # ধাপ ১ এর ভিউটি এখানে ইম্পোর্ট করুন

urlpatterns = [
    path('admin/', admin.site.urls),
# পুরানো TemplateView এর বদলে এই লাইনটি দিন:
    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
]
