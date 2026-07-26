import secrets
import string

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MinValueValidator
from django.db import models


SECURITY_QUESTION = "What is your dream place ?"
DEFAULT_SECURITY_ANSWER = "Kathmandu"


def normalize_security_answer(answer):
    return " ".join(str(answer).strip().lower().split())


class UserSecurityAnswer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="security_answer")
    question = models.CharField(max_length=150, default=SECURITY_QUESTION)
    answer_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def set_answer(self, answer):
        self.answer_hash = make_password(normalize_security_answer(answer))

    def check_answer(self, answer):
        return check_password(normalize_security_answer(answer), self.answer_hash)

    def __str__(self):
        return f"Security answer for {self.user.username}"


class Expense(models.Model):
    CATEGORY_FOOD = "Food"
    CATEGORY_TRANSPORT = "Transport"
    CATEGORY_RENT = "Rent"
    CATEGORY_EDUCATION = "Education"
    CATEGORY_HEALTH = "Health"
    CATEGORY_SHOPPING = "Shopping"
    CATEGORY_ENTERTAINMENT = "Entertainment"
    CATEGORY_BILLS = "Bills"
    CATEGORY_FAMILY = "Family"
    CATEGORY_OTHER = "Other"

    CATEGORY_CHOICES = [
        (CATEGORY_FOOD, "Food"),
        (CATEGORY_TRANSPORT, "Transport"),
        (CATEGORY_RENT, "Rent"),
        (CATEGORY_EDUCATION, "Education"),
        (CATEGORY_HEALTH, "Health"),
        (CATEGORY_SHOPPING, "Shopping"),
        (CATEGORY_ENTERTAINMENT, "Entertainment"),
        (CATEGORY_BILLS, "Bills"),
        (CATEGORY_FAMILY, "Family"),
        (CATEGORY_OTHER, "Other"),
    ]

    PAYMENT_CASH = "Cash"
    PAYMENT_BANK = "Bank"
    PAYMENT_CARD = "Card"
    PAYMENT_WALLET = "Online Wallet"
    PAYMENT_OTHER = "Other"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_CASH, "Cash"),
        (PAYMENT_BANK, "Bank"),
        (PAYMENT_CARD, "Card"),
        (PAYMENT_WALLET, "Online Wallet"),
        (PAYMENT_OTHER, "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    date = models.DateField()
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_CASH)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.amount}"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month"]
        constraints = [
            models.UniqueConstraint(fields=["user", "month", "year"], name="unique_user_monthly_budget"),
        ]

    def __str__(self):
        return f"{self.user.username} budget {self.month}/{self.year}"


class FamilyGroup(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=12, unique=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_family_groups")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    @classmethod
    def generate_unique_code(cls):
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(8))
            if not cls.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return self.name


class FamilyBudget(models.Model):
    family_group = models.ForeignKey(FamilyGroup, on_delete=models.CASCADE, related_name="budgets")
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month"]
        constraints = [
            models.UniqueConstraint(fields=["family_group", "month", "year"], name="unique_family_monthly_budget"),
        ]

    def __str__(self):
        return f"{self.family_group.name} budget {self.month}/{self.year}"


class FamilyMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="family_memberships")
    family_group = models.ForeignKey(FamilyGroup, on_delete=models.CASCADE, related_name="memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["family_group__name", "user__username"]
        constraints = [
            models.UniqueConstraint(fields=["user", "family_group"], name="unique_family_membership"),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.family_group.name}"


class RecurringExpense(models.Model):
    FREQUENCY_DAILY = "daily"
    FREQUENCY_WEEKLY = "weekly"
    FREQUENCY_MONTHLY = "monthly"
    FREQUENCY_YEARLY = "yearly"

    FREQUENCY_CHOICES = [
        (FREQUENCY_DAILY, "Daily"),
        (FREQUENCY_WEEKLY, "Weekly"),
        (FREQUENCY_MONTHLY, "Monthly"),
        (FREQUENCY_YEARLY, "Yearly"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recurring_expenses")
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    category = models.CharField(max_length=30, choices=Expense.CATEGORY_CHOICES, default=Expense.CATEGORY_OTHER)
    payment_method = models.CharField(
        max_length=30,
        choices=Expense.PAYMENT_METHOD_CHOICES,
        default=Expense.PAYMENT_CASH,
    )
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default=FREQUENCY_MONTHLY)
    next_due_date = models.DateField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_due_date", "title"]

    def __str__(self):
        return f"{self.title} ({self.get_frequency_display()})"


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    email_budget_alerts = models.BooleanField(default=True)
    email_family_alerts = models.BooleanField(default=True)
    email_daily_summary = models.BooleanField(default=False)
    email_weekly_summary = models.BooleanField(default=False)
    email_monthly_report = models.BooleanField(default=False)
    email_payment_reminders = models.BooleanField(default=True)
    email_unexpected_spending = models.BooleanField(default=True)
    last_budget_alert_percent = models.PositiveSmallIntegerField(default=0)
    last_family_budget_alert_percent = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user.username}"

class AlertLog(models.Model):
    ALERT_TYPES = (
        ('budget_personal', 'Personal Budget Threshold'),
        ('budget_family', 'Family Budget Threshold'),
        ('unexpected', 'Unexpected Spending'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alert_logs')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)  # store threshold, amount, etc.

    class Meta:
        ordering = ['-sent_at']
