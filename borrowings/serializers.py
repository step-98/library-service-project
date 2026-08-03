from rest_framework import serializers
from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing


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
        book.save()
        instance = super().create(validated_data)
        return instance
