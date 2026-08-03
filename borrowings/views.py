from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingDetailSerializer


class BorrowingViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated,]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        else:
            return BorrowingSerializer
