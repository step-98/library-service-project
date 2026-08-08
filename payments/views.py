import os
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from borrowings.telegram import send_telegram_notification
from rest_framework.views import APIView
from stripe import StripeClient
from rest_framework.decorators import action
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.stripe import create_stripe_session


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        payment = Payment.objects.all()
        if not self.request.user.is_staff:
            payment = payment.filter(borrowing__user=self.request.user)
            return payment

        return payment

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path="renew",
    )
    def renew(self, request, pk=None):
        payment = self.get_object()

        if payment.status != Payment.Status.EXPIRED:
            raise ValidationError({"detail": "Payment doesn't have to be renewed."})
        else:
            stripe_session = create_stripe_session(payment.borrowing.book, self.request, payment.money_to_pay)
            Payment.objects.filter(pk=payment.id).update(
                session_url=stripe_session["session_url"],
                session_id=stripe_session["session_id"],
                status=Payment.Status.PENDING,
            )
            return Response({"detail": "Payment has been successfully renewed"})


class PaymentCancelView(APIView):
    def get(self, request):
        return Response({"detail": "Payment can be completed later. The session is still available for 24 hours."})


class PaymentSuccessView(APIView):
    def get(self, request):
        session_id = request.query_params.get("session_id", None)
        payment = get_object_or_404(Payment, session_id=session_id)
        client = StripeClient(os.environ.get("STRIPE_SECRET_KEY"))
        session = client.v1.checkout.sessions.retrieve(session_id)
        if session.payment_status == "paid" and payment.status != Payment.Status.PAID:
            payment.status = Payment.Status.PAID
            payment.save()
            send_telegram_notification(
                f"Payment: {payment.id}"
                f"\nuser: {payment.borrowing.user}"
                f"\nbook: {payment.borrowing.book.title}"
                f"\nstatus: {payment.status}"
                f"\npaid: {payment.money_to_pay} USD",)
        return Response({"detail": "Payment has been successfully completed"})
