import datetime

from django.db.utils import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer
from payments.models import Payment

BORROWING_URL = reverse("borrowings:borrowing-list")


def sample_book(**params) -> Book:
    defaults = {
        "title": "test",
        "author": "test",
        "cover": "SOFT",
        "inventory": 5,
        "daily_fee": 5,
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def sample_borrowing(**params) -> Borrowing:
    if "book" not in params:
        params["book"] = sample_book()
    if "user" not in params:
        user, _ = get_user_model().objects.get_or_create(
            email="sample_borrower@test.com", defaults={"password": "test1234"}
        )
        params["user"] = user

    defaults = {
        "expected_return_date": timezone.localdate() + datetime.timedelta(days=5),
        "actual_return_date": None,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


class UnauthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test1234",
        )
        self.client.force_authenticate(user=self.user)

    def test_borrowing_list(self):
        sample_borrowing(user=self.user)
        sample_borrowing()

        borrowings = Borrowing.objects.filter(user=self.user)
        serializer = BorrowingSerializer(borrowings, many=True)
        res = self.client.get(BORROWING_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_return_date_not_in_past(self):
        yesterday = timezone.localdate() - datetime.timedelta(days=1)
        with self.assertRaises(IntegrityError):
            sample_borrowing(expected_return_date=yesterday)

    def test_return_borrowing_on_time(self):
        book = sample_book(inventory=5)
        borrowing = sample_borrowing(
            user=self.user,
            book=book,
            expected_return_date=timezone.localdate() + datetime.timedelta(days=2),
            actual_return_date=None,
        )
        url = reverse("borrowings:borrowing-return", args=[borrowing.id])
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        borrowing.refresh_from_db()
        book.refresh_from_db()

        self.assertEqual(borrowing.actual_return_date, timezone.localdate())
        self.assertEqual(book.inventory, 6)
        self.assertFalse(Payment.objects.filter(borrowing=borrowing).exists())
