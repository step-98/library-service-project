from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

import borrowings
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingDetailSerializer, BorrowingCreateSerializer


class BorrowingViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated,]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        elif self.action == "create":
            return BorrowingCreateSerializer
        else:
            return BorrowingSerializer

    def get_queryset(self):
        borrowing = Borrowing.objects.all()
        is_active = self.request.query_params.get("is_active", None)
        if is_active and is_active.lower() == "true":
            borrowing = borrowing.filter(actual_return_date__isnull=True)
        if self.request.user.is_staff:
            user_id =self.request.query_params.get("user_id", None)
            if user_id:
                borrowing = borrowing.filter(user_id=user_id)
            return borrowing

        return borrowing.filter(user=self.request.user)
