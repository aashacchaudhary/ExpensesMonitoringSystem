from django.contrib import admin

from .models import Budget, Expense, FamilyBudget, FamilyGroup, FamilyMembership, UserSecurityAnswer


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "amount", "category", "payment_method", "date")
    list_filter = ("category", "payment_method", "date")
    search_fields = ("title", "description", "user__username", "user__email")
    date_hierarchy = "date"


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "month", "year", "amount", "updated_at")
    list_filter = ("month", "year")
    search_fields = ("user__username", "user__email")


@admin.register(UserSecurityAnswer)
class UserSecurityAnswerAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "updated_at")
    search_fields = ("user__username", "user__email", "question")
    readonly_fields = ("answer_hash",)


@admin.register(FamilyBudget)
class FamilyBudgetAdmin(admin.ModelAdmin):
    list_display = ("family_group", "month", "year", "amount", "updated_at")
    list_filter = ("month", "year")
    search_fields = ("family_group__name", "family_group__code")


class FamilyMembershipInline(admin.TabularInline):
    model = FamilyMembership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(FamilyGroup)
class FamilyGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_by", "created_at")
    search_fields = ("name", "code", "created_by__username")
    inlines = (FamilyMembershipInline,)


@admin.register(FamilyMembership)
class FamilyMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "family_group", "joined_at")
    list_filter = ("family_group",)
    search_fields = ("user__username", "family_group__name", "family_group__code")

from .models import UserSettings, AlertLog, RecurringExpense

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_budget_alerts', 'email_daily_summary', 'email_monthly_report')
    search_fields = ('user__username',)

@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert_type', 'sent_at')
    list_filter = ('alert_type',)

@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'amount', 'next_due_date', 'is_active')
    list_filter = ('is_active', 'frequency')