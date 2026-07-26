# expenses/signals.py

from decimal import Decimal
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Expense, Budget, FamilyBudget, FamilyMembership, UserSettings, AlertLog
from .utils import get_monthly_total, get_family_monthly_total

def send_alert_email(user, subject, template_name, context):
    if not user.email:
        return
    context.update({'site_url': settings.SITE_URL, 'user': user})
    html = render_to_string(f'emails/{template_name}', context)
    plain = strip_tags(html)
    send_mail(
        subject,
        plain,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html,
        fail_silently=True,
    )

@receiver(post_save, sender=Expense)
def check_budget_thresholds(sender, instance, created, **kwargs):
    if not created:
        return
    user = instance.user
    today = timezone.now().date()
    # Personal budget
    total = get_monthly_total(user, today.year, today.month)
    budget = Budget.objects.filter(user=user, month=today.month, year=today.year).first()
    if budget and budget.amount > 0:
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)
        if settings_obj.email_budget_alerts:
            percent = (total / budget.amount) * 100
            last = settings_obj.last_budget_alert_percent
            # Send if crossing 75, 90, 100
            if percent >= 100 and last < 100:
                send_alert_email(user, 'Budget Alert: Limit Exceeded!', 'budget_alert.html',
                                 {'budget': budget, 'total': total, 'percent': 100, 'remaining': budget.amount - total})
                settings_obj.last_budget_alert_percent = 100
            elif percent >= 90 and last < 90:
                send_alert_email(user, 'Budget Alert: 90% Used', 'budget_alert.html',
                                 {'budget': budget, 'total': total, 'percent': 90, 'remaining': budget.amount - total})
                settings_obj.last_budget_alert_percent = 90
            elif percent >= 75 and last < 75:
                send_alert_email(user, 'Budget Alert: 75% Used', 'budget_alert.html',
                                 {'budget': budget, 'total': total, 'percent': 75, 'remaining': budget.amount - total})
                settings_obj.last_budget_alert_percent = 75
            settings_obj.save()

    # Family budget alerts
    memberships = FamilyMembership.objects.filter(user=user)
    for membership in memberships:
        group = membership.family_group
        family_total = get_family_monthly_total(group, today.year, today.month)
        family_budget = FamilyBudget.objects.filter(family_group=group, month=today.month, year=today.year).first()
        if family_budget and family_budget.amount > 0:
            # We'll send alert to all members if enabled
            members = FamilyMembership.objects.filter(family_group=group).select_related('user')
            percent = (family_total / family_budget.amount) * 100
            # To avoid duplicates, we track per user and per group? We'll use AlertLog.
            # But we need to check each user's preference separately.
            for member in members:
                member_user = member.user
                settings_obj, _ = UserSettings.objects.get_or_create(user=member_user)
                if settings_obj.email_family_alerts:
                    # Use AlertLog to avoid duplicate for the same threshold across the group.
                    # Simple approach: check if we already sent for this threshold and group.
                    # We'll create a helper function.
                    last = settings_obj.last_family_budget_alert_percent
                    if percent >= 100 and last < 100:
                        send_alert_email(member_user, f'Family Budget Alert: {group.name} Over Limit!',
                                         'family_alert.html',
                                         {'group': group, 'budget': family_budget, 'total': family_total,
                                          'percent': 100, 'remaining': family_budget.amount - family_total})
                        settings_obj.last_family_budget_alert_percent = 100
                    elif percent >= 90 and last < 90:
                        send_alert_email(member_user, f'Family Budget Alert: {group.name} 90% Used',
                                         'family_alert.html',
                                         {'group': group, 'budget': family_budget, 'total': family_total,
                                          'percent': 90, 'remaining': family_budget.amount - family_total})
                        settings_obj.last_family_budget_alert_percent = 90
                    elif percent >= 75 and last < 75:
                        send_alert_email(member_user, f'Family Budget Alert: {group.name} 75% Used',
                                         'family_alert.html',
                                         {'group': group, 'budget': family_budget, 'total': family_total,
                                          'percent': 75, 'remaining': family_budget.amount - family_total})
                        settings_obj.last_family_budget_alert_percent = 75
                    settings_obj.save()

    # Unexpected spending alert: daily expense > 200% of average daily of last 7 days
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    if settings_obj.email_unexpected_spending:
        today = timezone.now().date()
        # Get last 7 days (excluding today) total and average
        start = today - timezone.timedelta(days=7)
        recent = Expense.objects.filter(user=user, date__gte=start, date__lt=today)
        count = recent.count()
        if count > 0:
            avg = recent.aggregate(total=Sum('amount'))['total'] / count
            # Check today's total so far (including this expense)
            today_total = get_monthly_total(user, today.year, today.month, day=today.day)  # we'll need a function
            # We'll compute daily total for today
            today_expenses = Expense.objects.filter(user=user, date=today)
            today_sum = today_expenses.aggregate(total=Sum('amount'))['total'] or 0
            if avg > 0 and today_sum > avg * 2:
                send_alert_email(user, 'Unexpected High Spending Alert', 'unexpected_spending.html',
                                 {'avg': avg, 'today_total': today_sum, 'date': today})