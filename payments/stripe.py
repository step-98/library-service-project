import os
from stripe import StripeClient
from django.utils import timezone
from django.urls import reverse

def create_stripe_session(
        validated_data,
        request
):
    client = StripeClient(os.environ.get("STRIPE_SECRET_KEY"))
    days = max((validated_data["expected_return_date"] - timezone.localdate()).days, 1)
    money_to_pay = days * validated_data["book"].daily_fee
    pay_in_cents = int(money_to_pay * 100)
    success_url = f"{request.build_absolute_uri(reverse('payments:success'))}?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.build_absolute_uri(reverse('payments:cancel'))}?session_id={{CHECKOUT_SESSION_ID}}"
    session = client.v1.checkout.sessions.create({
        "success_url": success_url,
        "cancel_url": cancel_url,
        "line_items": [{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": validated_data["book"].title,
                },
                "unit_amount": pay_in_cents
            },
            "quantity": 1
        }],
        "mode": "payment",
    })

    return {
    "session_url":session.url,
    "session_id":session.id,
    "money_to_pay":money_to_pay,
}

