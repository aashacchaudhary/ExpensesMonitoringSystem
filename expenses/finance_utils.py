import math


def calculate_emi(principal, annual_rate, months):
    if months <= 0:
        return 0.0
    if annual_rate <= 0:
        return principal / months

    rate = annual_rate / 12 / 100
    numerator = principal * rate * math.pow(1 + rate, months)
    denominator = math.pow(1 + rate, months) - 1
    return numerator / denominator


def amortization_schedule(principal, annual_rate, months):
    if months <= 0:
        return []

    emi = calculate_emi(principal, annual_rate, months)
    if annual_rate <= 0:
        balance = principal
        principal_paid = principal / months
        schedule = []
        for month in range(1, months + 1):
            balance = max(0.0, balance - principal_paid)
            schedule.append(
                {
                    "month": month,
                    "emi": emi,
                    "interest": 0.0,
                    "principal": principal_paid,
                    "balance": balance,
                }
            )
        return schedule

    rate = annual_rate / 12 / 100
    balance = principal
    schedule = []
    for month in range(1, months + 1):
        interest = balance * rate
        principal_paid = emi - interest
        balance = max(0.0, balance - principal_paid)
        schedule.append(
            {
                "month": month,
                "emi": emi,
                "interest": interest,
                "principal": principal_paid,
                "balance": balance,
            }
        )
    return schedule


def future_value(present_value, annual_rate, years, compounding_per_year=12):
    if years <= 0 or annual_rate <= 0:
        return present_value
    rate = annual_rate / 100 / compounding_per_year
    periods = years * compounding_per_year
    return present_value * math.pow(1 + rate, periods)
