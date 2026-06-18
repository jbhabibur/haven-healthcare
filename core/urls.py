from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from .views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('appointments/', include('appointments.urls')),
]
