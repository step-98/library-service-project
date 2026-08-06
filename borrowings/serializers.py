import os
from django.utils import timezone

from rest_framework import serializers
from stripe import StripeClient

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from borrowings.telegram import send_telegram_notification
from django.db import transaction

from payments.models import Payment


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
        book.inventory -= 1
        days = max((validated_data["expected_return_date"] - timezone.localdate()).days, 1)
        money_to_pay = days * book.daily_fee
        pay_in_cents = int(money_to_pay * 100)
        client = StripeClient(os.environ.get("STRIPE_SECRET_KEY"))
        session = client.v1.checkout.sessions.create({
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
            "line_items": [{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": book.title,
                    },
                    "unit_amount": pay_in_cents
                },
                "quantity": 1
            }],
            "mode": "payment",
        })
        with transaction.atomic():
            book.save()
            instance = super().create(validated_data)

            Payment.objects.create(
                borrowing=instance,
                session_url=session.url,
                session_id=session.id,
                money_to_pay=money_to_pay,
            )
        send_telegram_notification(
            f"User: {user}"
            f"\nborrowed book: {book.title}"
            f"\nexpected return date: {instance.expected_return_date}",
        )
        return instance
