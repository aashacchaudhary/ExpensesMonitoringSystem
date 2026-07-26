from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
from expenses.models import Expense
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send weekly expense summary to users who opted in'

    def handle(self, *args, **options):
        today = timezone.now().date()
        start_date = today - timedelta(days=7)
        users = User.objects.filter(settings__email_weekly_summary=True)
        for user in users:
            expenses = Expense.objects.filter(user=user, date__gte=start_date, date__lt=today)
            total = expenses.aggregate(total=Sum('amount'))['total'] or 0
            if total == 0:
                continue
            context = {
                'user': user,
                'expenses': expenses,
                'total': total,
                'start_date': start_date,
                'end_date': today - timedelta(days=1),
                'site_url': settings.SITE_URL,
            }
            html = render_to_string('emails/weekly_summary.html', context)
            plain = strip_tags(html)
            send_mail(
                f'Your weekly expense summary ({start_date} – {today - timedelta(days=1)})',
                plain,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html,
                fail_silently=True,
            )
            self.stdout.write(f'Sent weekly summary to {user.email}')