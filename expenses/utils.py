# expenses/utils.py

from decimal import Decimal
from django.db.models import Sum
from .models import Expense

def get_monthly_total(user, year, month, day=None):
    qs = Expense.objects.filter(user=user, date__year=year, date__month=month)
    if day is not None:
        qs = qs.filter(date__day=day)
    total = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    return total

def get_family_monthly_total(family_group, year, month):
    member_ids = family_group.memberships.values_list('user_id', flat=True)
    total = Expense.objects.filter(user_id__in=member_ids, date__year=year, date__month=month) \
                           .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    return total