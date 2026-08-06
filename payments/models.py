from django.db import models
from django.utils.translation import gettext_lazy as _

from borrowings.models import Borrowing


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PAID = "PAID", _("Paid")

    class Type(models.TextChoices):
        PAYMENT = "PAYMENT", _("Payment")
        FINE = "FINE", _("Fine")

    status = models.CharField(choices=Status, default=Status.PENDING, max_length=10)
    type = models.CharField(choices=Type, default=Type.PAYMENT, max_length=10)
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE , related_name="payments")
    session_url = models.URLField()
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)