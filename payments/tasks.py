import os
from stripe import StripeClient
from payments.models import Payment
from celery import shared_task




@shared_task
def expiring_sessions() -> None:
    payments = Payment.objects.filter(
        status=Payment.Status.PENDING,
    )
    if payments.exists():
        client = StripeClient(os.environ.get("STRIPE_SECRET_KEY"))
        for payment in payments:
            session = client.v1.checkout.sessions.retrieve(session_id=payment.session_id)
            if session.status == "expired":
                payment.status = Payment.Status.EXPIRED
                payment.save()
