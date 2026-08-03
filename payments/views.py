import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.generic import View, TemplateView
from django.shortcuts import redirect

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        # Dynamically get the domain from settings to ensure it works in different environments
        YOUR_DOMAIN = settings.SITE_URL
        
        try:
            # Create a dummy session and price ($25.00) for free testing
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Haven Healthcare Medical Package',
                            },
                            'unit_amount': 2500, # 2500 cents = $25.00 USD
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=YOUR_DOMAIN + '/payments/success/',
                cancel_url=YOUR_DOMAIN + '/payments/cancel/',
            )
            # Redirect directly to Stripe's hosted checkout page
            return redirect(checkout_session.url, code=303)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class PaymentSuccessView(TemplateView):
    template_name = "payments/success.html"

class PaymentCancelView(TemplateView):
    template_name = "payments/cancel.html"