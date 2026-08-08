from django.db import transaction
from django.db.models import F
from django.utils import timezone
from books.models import Book
from rest_framework import viewsets, mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingDetailSerializer, BorrowingCreateSerializer
from rest_framework.decorators import action

from payments.models import Payment
from payments.stripe import create_stripe_session

FINE_MULTIPLIER = 2

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

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path="return",
    )
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            raise ValidationError({"actual_return_date": "The borrowing can be returned only once"})

        actual_return_date = timezone.localdate()
        money_to_pay = None
        stripe_session = None

        if actual_return_date > borrowing.expected_return_date:
            overdue_days = (actual_return_date - borrowing.expected_return_date).days
            money_to_pay = overdue_days * borrowing.book.daily_fee * FINE_MULTIPLIER
            stripe_session = create_stripe_session(borrowing.book, self.request, money_to_pay)

        with transaction.atomic():
            borrowing.actual_return_date = actual_return_date
            Book.objects.filter(pk=borrowing.book.id).update(
                inventory=F("inventory") + 1,
            )
            borrowing.save()

            if stripe_session:
                Payment.objects.create(
                    borrowing=borrowing,
                    session_url=stripe_session["session_url"],
                    session_id=stripe_session["session_id"],
                    money_to_pay=money_to_pay,
                    type=Payment.Type.FINE,
                )


        serializer = BorrowingSerializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)
