from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

User = get_user_model()


class UserCreationTests(TestCase):
    def test_create_user_with_hashed_password(self):
        url = reverse("users:create")
        user_data = {
            "email": "test@test.com",
            "password": "test1234",
        }
        response = self.client.post(url, user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=user_data["email"]).exists())
        user = User.objects.get(email=user_data["email"])

        self.assertNotEqual(user.password, user_data["password"])
        self.assertTrue(user.check_password(user_data["password"]))
