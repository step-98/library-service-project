from rest_framework import serializers
from payments.stripe import create_stripe_session
from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from borrowings.telegram import send_telegram_notification
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from payments.models import Payment
from payments.serializers import PaymentSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingDetailSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    payments = PaymentSerializer(read_only=True, many=True)
    class Meta(BorrowingSerializer.Meta):
        fields = BorrowingSerializer.Meta.fields + ("payments",)


class BorrowingCreateSerializer(BorrowingSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "expected_return_date",
            "book",
        )

    def validate_book(self, value):
        if value.inventory <= 0:
            raise serializers.ValidationError(
                "There is no more books in the inventory."
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user
        book = validated_data["book"]
        days = max((validated_data["expected_return_date"] - timezone.localdate()).days, 1)
        money_to_pay = days * validated_data["book"].daily_fee
        stripe_session = create_stripe_session(book, self.context["request"], money_to_pay)

        with transaction.atomic():
            Book.objects.filter(pk=book.id).update(
                inventory=F("inventory") - 1,
            )
            book.refresh_from_db()
            instance = super().create(validated_data)

            Payment.objects.create(
                borrowing=instance,
                session_url=stripe_session["session_url"],
                session_id=stripe_session["session_id"],
                money_to_pay=money_to_pay,
            )
        send_telegram_notification(
            f"User: {user}"
            f"\nborrowed book: {book.title}"
            f"\nexpected return date: {instance.expected_return_date}",
        )
        return instance
