from django.utils import timezone
from borrowings.telegram import send_telegram_notification
from borrowings.models import Borrowing
from celery import shared_task


@shared_task
def overdue_borrowings() -> None:
    borrowings = Borrowing.objects.filter(
        expected_return_date__lte=timezone.localdate(),
        actual_return_date__isnull=True
    )
    if borrowings.exists():
        send_telegram_notification("Today's borrowings overdue:")
        for borrowing in borrowings:
            send_telegram_notification(
                f"User: {borrowing.user}"
                f"\nborrowed book: {borrowing.book.title}"
                f"\nexpected return date: {borrowing.expected_return_date}"
            )
    else:
        send_telegram_notification("No borrowings overdue today!")
