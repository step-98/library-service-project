import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import PaymentSerializer

PAYMENT_URL = reverse("payments:payment-list")


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


def sample_payment(**params) -> Payment:
    if "borrowing" not in params:
        params["borrowing"] = sample_borrowing()

    defaults = {
        "status": Payment.Status.PENDING,
        "type": Payment.Type.PAYMENT,
        "session_url": "https://example.com/success",
        "session_id": "1",
        "money_to_pay": 10,
    }
    defaults.update(params)
    return Payment.objects.create(**defaults)


class AuthenticatedPaymentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test1234",
        )
        self.client.force_authenticate(user=self.user)

    def test_payment_list(self):
        user_borrowing = sample_borrowing(user=self.user)
        sample_payment(borrowing=user_borrowing)
        sample_payment()

        payments = Payment.objects.filter(borrowing__user=self.user)
        serializer = PaymentSerializer(payments, many=True)
        res = self.client.get(PAYMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 1)
