from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

import borrowings
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
