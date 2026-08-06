import os
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.views import APIView
from stripe import StripeClient

from payments.models import Payment
from payments.serializers import PaymentSerializer


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


class PaymentCancelView(APIView):
    def get(self, request):
        return Response({"detail": "Payment can be completed later. The session is still available for 24 hours."})


class PaymentSuccessView(APIView):
    def get(self, request):
        session_id = request.query_params.get("session_id", None)
        payment = get_object_or_404(Payment, session_id=session_id)
        client = StripeClient(os.environ.get("STRIPE_SECRET_KEY"))
        session = client.v1.checkout.sessions.retrieve(session_id)
        if session.payment_status == "paid":
            payment.status = Payment.Status.PAID
            payment.save()
        return Response({"detail": "Payment has been successfully completed"})
