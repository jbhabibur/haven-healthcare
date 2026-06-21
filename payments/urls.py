from django.urls import path
from .views import CreateCheckoutSessionView, PaymentSuccessView, PaymentCancelView

app_name = 'payments'

urlpatterns = [
    path('checkout/', CreateCheckoutSessionView.as_view(), name='stripe-checkout'),
    path('success/', PaymentSuccessView.as_view(), name='payment-success'),
    path('cancel/', PaymentCancelView.as_view(), name='payment-cancel'),
]