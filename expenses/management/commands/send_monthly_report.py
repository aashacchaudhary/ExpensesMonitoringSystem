from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings as django_settings
from django.db.models import Sum
from expenses.models import Expense, Budget
from expenses.pdf_builder import build_statement_pdf
from expenses.utils import get_monthly_total
from expenses.views import category_summary, daily_summary  # or move helpers to utils
import calendar

class Command(BaseCommand):
    help = 'Send end-of-month report PDF to users who opted in'

    def handle(self, *args, **options):
        today = timezone.now().date()
        if today.month == 1:
            month = 12
            year = today.year - 1
        else:
            month = today.month - 1
            year = today.year
        users = User.objects.filter(settings__email_monthly_report=True)
        for user in users:
            expenses = Expense.objects.filter(user=user, date__month=month, date__year=year)
            total = get_monthly_total(user, year, month)
            if total == 0:
                continue
            budget = Budget.objects.filter(user=user, month=month, year=year).first()
            categories = category_summary(expenses)
            # Build PDF
            pdf_content = build_statement_pdf(
                title='Monthly Expense Report',
                subtitle=f'Statement for {calendar.month_name[month]} {year}',
                details=[
                    ('Account holder', user.username),
                    ('Email', user.email or '-'),
                    ('Statement period', f'{calendar.month_name[month]} {year}'),
                    ('Records', expenses.count()),
                ],
                summary_cards=[
                    {'label': 'Total Spent', 'value': f'{total:.2f}', 'note': 'Statement total', 'color': (255,107,107)},
                    {'label': 'Budget', 'value': f'{budget.amount:.2f}' if budget else 'Not set', 'note': 'Carries forward', 'color': (22,160,133)},
                ],
                charts=[
                    {'type': 'bar', 'title': 'Category-wise', 'labels': [c['label'] for c in categories], 'values': [float(c['total']) for c in categories]},
                ],
                table_title='Transactions',
                table_headers=['Date', 'Title', 'Category', 'Amount'],
                table_rows=[[e.date, e.title, e.category, f'{e.amount:.2f}'] for e in expenses],
                table_widths=[60, 100, 80, 60]
            )
            subject = f'Monthly Expense Report for {calendar.month_name[month]} {year}'
            context = {'user': user, 'month': calendar.month_name[month], 'year': year, 'site_url': django_settings.SITE_URL}
            html = render_to_string('emails/monthly_report_email.html', context)
            plain = strip_tags(html)
            msg = EmailMultiAlternatives(subject, plain, django_settings.DEFAULT_FROM_EMAIL, [user.email])
            msg.attach_alternative(html, "text/html")
            msg.attach(f'expense_report_{year}_{month:02d}.pdf', pdf_content, 'application/pdf')
            msg.send(fail_silently=True)
            self.stdout.write(f'Sent monthly report to {user.email}')
            