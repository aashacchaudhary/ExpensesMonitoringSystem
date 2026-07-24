import datetime
import calendar

from django.core.management.base import BaseCommand

from expenses.models import Expense, RecurringExpense


def next_due_date(current_date, frequency):
    if frequency == RecurringExpense.FREQUENCY_DAILY:
        return current_date + datetime.timedelta(days=1)
    if frequency == RecurringExpense.FREQUENCY_WEEKLY:
        return current_date + datetime.timedelta(days=7)
    if frequency == RecurringExpense.FREQUENCY_YEARLY:
        next_year = current_date.year + 1
        next_day = min(current_date.day, calendar.monthrange(next_year, current_date.month)[1])
        return datetime.date(next_year, current_date.month, next_day)

    next_month = current_date.month + 1
    next_year = current_date.year
    if next_month > 12:
        next_month = 1
        next_year += 1
    next_day = min(current_date.day, calendar.monthrange(next_year, next_month)[1])
    return datetime.date(next_year, next_month, next_day)


class Command(BaseCommand):
    help = "Generate expense entries from active recurring expenses due on or before today."

    def handle(self, *args, **options):
        today = datetime.date.today()
        due_items = RecurringExpense.objects.filter(is_active=True, next_due_date__lte=today).select_related("user")
        created_count = 0

        for recurring in due_items:
            Expense.objects.create(
                user=recurring.user,
                title=recurring.title,
                amount=recurring.amount,
                category=recurring.category,
                payment_method=recurring.payment_method,
                date=today,
                description=f"Auto-generated from recurring expense #{recurring.pk}.",
            )
            recurring.next_due_date = next_due_date(recurring.next_due_date, recurring.frequency)
            recurring.save(update_fields=["next_due_date", "updated_at"])
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} expenses from recurring entries."))
