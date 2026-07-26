import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0003_usersecurityanswer"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RecurringExpense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150)),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0.01)],
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("Food", "Food"),
                            ("Transport", "Transport"),
                            ("Rent", "Rent"),
                            ("Education", "Education"),
                            ("Health", "Health"),
                            ("Shopping", "Shopping"),
                            ("Entertainment", "Entertainment"),
                            ("Bills", "Bills"),
                            ("Family", "Family"),
                            ("Other", "Other"),
                        ],
                        default="Other",
                        max_length=30,
                    ),
                ),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("Cash", "Cash"),
                            ("Bank", "Bank"),
                            ("Card", "Card"),
                            ("Online Wallet", "Online Wallet"),
                            ("Other", "Other"),
                        ],
                        default="Cash",
                        max_length=30,
                    ),
                ),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                            ("yearly", "Yearly"),
                        ],
                        default="monthly",
                        max_length=10,
                    ),
                ),
                ("next_due_date", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recurring_expenses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["next_due_date", "title"]},
        ),
    ]
