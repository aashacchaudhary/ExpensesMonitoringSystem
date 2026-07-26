import datetime
from decimal import Decimal

from django.db.models import Sum

from .models import Expense


def get_monthly_totals(user, months_back=6):
    today = datetime.date.today()
    totals = []

    for offset in range(months_back - 1, -1, -1):
        month = today.month - offset
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        total = (
            Expense.objects.filter(user=user, date__year=year, date__month=month)
            .aggregate(total=Sum("amount"))
            .get("total")
            or Decimal("0.00")
        )
        totals.append(float(total))

    return totals


def linear_regression_forecast(values):
    n = len(values)
    if n < 2:
        return None

    x_values = list(range(n))
    sum_x = sum(x_values)
    sum_y = sum(values)
    sum_xy = sum(x_values[index] * values[index] for index in range(n))
    sum_x2 = sum(x * x for x in x_values)
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return None

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    prediction = intercept + slope * n
    return max(0.0, prediction)
