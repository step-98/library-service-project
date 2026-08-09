from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from books.models import Book
from books.serializers import BookSerializer

BOOK_URL = reverse("books:book-list")


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


def detail_url(book_id: int) -> str:
    return reverse("books:book-detail", args=[book_id])


class UnauthenticatedBookApiReaTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_not_required(self):
        res = self.client.get(BOOK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class AuthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test1234",
        )
        self.client.force_authenticate(user=self.user)

    def test_book_list(self):
        sample_book()
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        res = self.client.get(BOOK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_book_details(self):
        book = sample_book()

        url = detail_url(book.id)

        res = self.client.get(url)
        serializer = BookSerializer(book)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_book_forbidden(self):
        payload = {
            "title": "test",
            "author": "test",
            "cover": "SOFT",
            "inventory": 5,
            "daily_fee": 5,
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@admin.com", password="admin1234"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_book(self):
        payload = {
            "title": "test",
            "author": "test",
            "cover": "SOFT",
            "inventory": 5,
            "daily_fee": 5,
        }
        res = self.client.post(BOOK_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
