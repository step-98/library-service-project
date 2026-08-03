from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="borrowings")

    class Meta:
        ordering = ["borrow_date"]
        constraints = [
            CheckConstraint(
                condition=models.Q(expected_return_date__gte=models.F("borrow_date")),
                name="borrowing_expected_return_date_greater_than_borrow_date",
            ),
            CheckConstraint(
                condition=models.Q(actual_return_date__isnull=True) | models.Q(actual_return_date__gte=models.F("borrow_date")),
                name="actual_return_date_is_null_or_greater_than_borrow_date",
            )
        ]
