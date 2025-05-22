# payments/views.py

import stripe
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from orders.models import Order  # Assuming your Order model is here

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle Stripe event types
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        try:
            order = Order.objects.get(payment_intent_id=payment_intent['id'])
            order.status = 'Processing'  # Or 'Completed'
            order.save()
            print(f'Order {order.id} status updated to Processing')
        except Order.DoesNotExist:
            print(f'Order with payment_intent_id {payment_intent["id"]} not found')

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        try:
            order = Order.objects.get(payment_intent_id=payment_intent['id'])
            order.status = 'Payment Failed'
            order.save()
            print(f'Order {order.id} status updated to Payment Failed')
        except Order.DoesNotExist:
            print(f'Order with payment_intent_id {payment_intent["id"]} not found')

    return HttpResponse(status=200)
