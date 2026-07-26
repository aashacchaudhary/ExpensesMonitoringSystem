from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from expenses.models import RecurringExpense, UserSettings
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send payment reminders for recurring expenses due in the next 3 days'

    def handle(self, *args, **options):
        today = timezone.now().date()
        due_date = today + timedelta(days=3)
        expenses = RecurringExpense.objects.filter(is_active=True, next_due_date__lte=due_date, next_due_date__gte=today)
        for expense in expenses:
            user = expense.user
            settings_obj, _ = UserSettings.objects.get_or_create(user=user)
            if not settings_obj.email_payment_reminders:
                continue
            context = {
                'user': user,
                'expense': expense,
                'due_date': expense.next_due_date,
                'site_url': settings.SITE_URL,
            }
            html = render_to_string('emails/payment_reminder.html', context)
            plain = strip_tags(html)
            send_mail(
                f'Payment Reminder: {expense.title} due on {expense.next_due_date}',
                plain,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html,
                fail_silently=True,
            )
            self.stdout.write(f'Sent reminder for {expense.title} to {user.email}')
            