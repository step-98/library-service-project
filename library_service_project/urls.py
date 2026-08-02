from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("books/", include("books.urls", namespace="books")),
    path("users/", include("user.urls", namespace="users")),
]
