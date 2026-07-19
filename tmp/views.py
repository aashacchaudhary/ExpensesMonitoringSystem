import calendar
import csv
import datetime
import json
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from .forms import (
    BudgetForm,
    ExpenseForm,
    ExpenseSearchForm,
    FamilyBudgetForm,
    FamilyGroupForm,
    FamilyTransactionFilterForm,
    JoinFamilyForm,
    PasswordResetEmailForm,
    RegisterForm,
    ReportFilterForm,
    SecurityAnswerForm,
    StyledAuthenticationForm,
    StyledSetPasswordForm,
)
from .models import (
    Budget,
    DEFAULT_SECURITY_ANSWER,
    Expense,
    FamilyBudget,
    FamilyGroup,
    FamilyMembership,
    SECURITY_QUESTION,
    UserSecurityAnswer,
)
from .pdf_builder import AMBER, CORAL, GREEN, NAVY, TEAL, build_statement_pdf


def decimal_to_float(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return value


def sum_amount(queryset):
    return queryset.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")


def category_summary(queryset):
    rows = (
        queryset.values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total", "category")
    )
    return [
        {"label": row["category"], "total": row["total"], "value": decimal_to_float(row["total"])}
        for row in rows
    ]


def daily_summary(queryset):
    rows = (
        queryset.values("date")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )
    return [
        {
            "label": row["date"].strftime("%d %b"),
            "date": row["date"],
            "total": row["total"],
            "value": decimal_to_float(row["total"]),
        }
        for row in rows
    ]


def monthly_summary_for_year(queryset, year):
    rows = (
        queryset.filter(date__year=year)
        .values("date__month")
        .annotate(total=Sum("amount"))
        .order_by("date__month")
    )
    totals = {row["date__month"]: decimal_to_float(row["total"]) for row in rows}
    return {
        "labels": [calendar.month_abbr[index] for index in range(1, 13)],
        "values": [totals.get(index, 0.0) for index in range(1, 13)],
    }


def month_date_range(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, 1), datetime.date(year, month, last_day)


def effective_monthly_record(queryset, month, year):
    return (
        queryset.filter(Q(year__lt=year) | Q(year=year, month__lte=month))
        .order_by("-year", "-month")
        .first()
    )


def monthly_record_source_label(record, month, year):
    if not record:
        return "No budget set"
    if record.month == month and record.year == year:
        return "Active for this month"
    return f"Carried forward from {calendar.month_name[record.month]} {record.year}"


def can_manage_family_group(user, family_group):
    if not user.is_authenticated:
        return False
    if family_group.created_by_id == user.pk:
        return True
    return family_group.created_by.username == user.get_username()


def get_security_answer_profile(user):
    profile, created = UserSecurityAnswer.objects.get_or_create(
        user=user,
        defaults={"question": SECURITY_QUESTION, "answer_hash": ""},
    )
    if created or not profile.answer_hash:
        profile.question = SECURITY_QUESTION
        profile.set_answer(DEFAULT_SECURITY_ANSWER)
        profile.save()
    return profile


def clear_password_reset_session(request):
    for key in ("password_reset_user_id", "password_reset_verified"):
        request.session.pop(key, None)


def budget_alerts(budget, total_expense, subject="Budget"):
    if not budget:
        return []
    if budget.amount <= 0:
        return []

    used_percent = (total_expense / budget.amount) * Decimal("100")
    subject_lower = subject.lower()
    if used_percent >= 100:
        return [{"level": "danger", "message": f"{subject} exceeded for this month."}]
    if used_percent >= 90:
        return [{"level": "warning", "message": f"Warning: You are close to your {subject_lower} limit."}]
    if used_percent >= 75:
        return [{"level": "info", "message": f"You have used 75% of your monthly {subject_lower}."}]
    return []


def budget_mood(budget, total_expense):
    if not budget or budget.amount <= 0:
        return {
            "used_percent": 0.0,
            "ring_percent": 0.0,
            "label": "No Budget",
            "state": "safe",
        }

    used_percent = (total_expense / budget.amount) * Decimal("100")
    ring_percent = max(0.0, min(decimal_to_float(used_percent), 100.0))

    if used_percent > 90:
        label = "Over Budget"
        state = "over"
    elif used_percent > 75:
        label = "Risk"
        state = "risk"
    elif used_percent > 50:
        label = "Watch"
        state = "watch"
    else:
        label = "Safe"
        state = "safe"

    return {
        "used_percent": decimal_to_float(used_percent),
        "ring_percent": ring_percent,
        "label": label,
        "state": state,
    }


def chart_payload(labels, values):
    return json.loads(json.dumps({"labels": labels, "values": values}, cls=DjangoJSONEncoder))


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


def pdf_response(filename, content):
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def money(value):
    return f"{value:.2f}"


def percent_text(part, whole):
    if not whole or whole <= 0:
        return "-"
    return f"{decimal_to_float((part / whole) * Decimal('100')):.1f}%"


def budget_cards(total, budget, budget_label="Total Budget"):
    budget_amount = budget.amount if budget else None
    remaining = budget_amount - total if budget_amount is not None else None
    return [
        {"label": "Total Spent", "value": money(total), "note": "Statement total", "color": CORAL},
        {
            "label": budget_label,
            "value": money(budget_amount) if budget_amount is not None else "Not set",
            "note": "Carries forward",
            "color": TEAL,
        },
        {
            "label": "Budget Used",
            "value": percent_text(total, budget_amount),
            "note": "Spent vs budget",
            "color": AMBER,
        },
        {
            "label": "Remaining",
            "value": money(remaining) if remaining is not None else "Not set",
            "note": "After spending",
            "color": GREEN if remaining is None or remaining >= 0 else CORAL,
        },
    ]


def chart_from_summary(title, summary, chart_type="bar", color=TEAL):
    return {
        "type": chart_type,
        "title": title,
        "labels": [row["label"] for row in summary],
        "values": [row["value"] for row in summary],
        "color": color,
    }


def expense_statement_rows(expenses, include_member=False):
    rows = []
    for expense in expenses:
        row = [expense.date, expense.title, expense.category, expense.payment_method]
        if include_member:
            row.insert(1, expense.user.username)
        row.extend([expense.description or "-", money(expense.amount)])
        rows.append(row)
    return rows


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "expenses/home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            security_profile = UserSecurityAnswer(user=user, question=SECURITY_QUESTION)
            security_profile.set_answer(form.cleaned_data["security_answer"])
            security_profile.save()
            messages.success(request, f"Registration successful. Your User ID is {user.id}. You can use it to log in.")
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Please correct the highlighted registration errors.")
    else:
        form = RegisterForm()

    return render(request, "expenses/register.html", {"form": form})


class ExpenseLoginView(LoginView):
    template_name = "expenses/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("dashboard")

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


def password_reset_email(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(email__iexact=form.cleaned_data["email"]).first()
            if user:
                get_security_answer_profile(user)
                request.session["password_reset_user_id"] = user.pk
                request.session["password_reset_verified"] = False
                messages.info(request, "Answer your security question to continue.")
                return redirect("password_reset_security")
            messages.error(request, "No account was found with that Gmail or email address.")
    else:
        form = PasswordResetEmailForm()

    return render(request, "expenses/password_reset_email.html", {"form": form})


def password_reset_security(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    user_id = request.session.get("password_reset_user_id")
    if not user_id:
        messages.error(request, "Please enter your Gmail or email address first.")
        return redirect("password_reset_email")

    user = get_object_or_404(User, pk=user_id)
    security_profile = get_security_answer_profile(user)

    if request.method == "POST":
        form = SecurityAnswerForm(request.POST)
        if form.is_valid():
            if security_profile.check_answer(form.cleaned_data["answer"]):
                request.session["password_reset_verified"] = True
                messages.success(request, "Security answer verified. Set a new password.")
                return redirect("password_reset_confirm")
            messages.error(request, "Security answer did not match.")
    else:
        form = SecurityAnswerForm()

    return render(
        request,
        "expenses/password_reset_security.html",
        {"form": form, "email": user.email, "question": security_profile.question},
    )


def password_reset_confirm(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    user_id = request.session.get("password_reset_user_id")
    if not user_id or not request.session.get("password_reset_verified"):
        messages.error(request, "Please verify your security answer first.")
        return redirect("password_reset_email")

    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = StyledSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            clear_password_reset_session(request)
            messages.success(request, "Password changed successfully. You can log in now.")
            return redirect("login")
        messages.error(request, "Please correct the highlighted password fields.")
    else:
        form = StyledSetPasswordForm(user)

    return render(request, "expenses/password_reset_confirm.html", {"form": form})


@login_required
def dashboard(request):
    today = datetime.date.today()
    month_expenses = Expense.objects.filter(
        user=request.user,
        date__year=today.year,
        date__month=today.month,
    )
    today_expenses = month_expenses.filter(date=today)
    total_month = sum_amount(month_expenses)
    total_today = sum_amount(today_expenses)
    budget = effective_monthly_record(Budget.objects.filter(user=request.user), today.month, today.year)
    remaining_budget = budget.amount - total_month if budget else None
    categories = category_summary(month_expenses)
    daily = daily_summary(month_expenses)
    yearly = monthly_summary_for_year(Expense.objects.filter(user=request.user), today.year)
    highest_category = categories[0] if categories else None

    context = {
        "total_month": total_month,
        "total_today": total_today,
        "remaining_budget": remaining_budget,
        "remaining_budget_negative": remaining_budget is not None and remaining_budget < 0,
        "budget": budget,
        "budget_source_label": monthly_record_source_label(budget, today.month, today.year),
        "budget_mood": budget_mood(budget, total_month),
        "highest_category": highest_category,
        "expense_count": month_expenses.count(),
        "recent_expenses": Expense.objects.filter(user=request.user)[:6],
        "budget_alerts": budget_alerts(budget, total_month),
        "category_chart": chart_payload([row["label"] for row in categories], [row["value"] for row in categories]),
        "daily_chart": chart_payload([row["label"] for row in daily], [row["value"] for row in daily]),
        "monthly_chart": yearly,
    }
    return render(request, "expenses/dashboard.html", context)


@login_required
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, "Expense added successfully.")
            return redirect("expense_list")
        messages.error(request, "Please correct the highlighted expense fields.")
    else:
        form = ExpenseForm(initial={"date": datetime.date.today()})

    return render(request, "expenses/expense_form.html", {"form": form})


@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user)
    form = ExpenseSearchForm(request.GET or None)

    if form.is_valid():
        title = form.cleaned_data.get("title")
        category = form.cleaned_data.get("category")
        payment_method = form.cleaned_data.get("payment_method")
        date = form.cleaned_data.get("date")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        month = form.cleaned_data.get("month")
        year = form.cleaned_data.get("year")

        if title:
            expenses = expenses.filter(title__icontains=title)
        if category:
            expenses = expenses.filter(category=category)
        if payment_method:
            expenses = expenses.filter(payment_method=payment_method)
        if date:
            expenses = expenses.filter(date=date)
        if date_from:
            expenses = expenses.filter(date__gte=date_from)
        if date_to:
            expenses = expenses.filter(date__lte=date_to)
        if month:
            expenses = expenses.filter(date__month=int(month))
        if year:
            expenses = expenses.filter(date__year=int(year))

    context = {
        "expenses": expenses,
        "form": form,
        "filtered_total": sum_amount(expenses),
    }
    return render(request, "expenses/expense_list.html", context)


@login_required
@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    messages.success(request, "Expense deleted successfully.")
    return redirect("expense_list")


@login_required
def monthly_report(request):
    form = ReportFilterForm(request.GET or None)
    today = datetime.date.today()
    month = today.month
    year = today.year

    if form.is_valid():
        month = int(form.cleaned_data["month"])
        year = int(form.cleaned_data["year"])

    expenses = Expense.objects.filter(user=request.user, date__month=month, date__year=year)
    categories = category_summary(expenses)
    daily = daily_summary(expenses)
    highest_category = categories[0] if categories else None
    total = sum_amount(expenses)
    budget = effective_monthly_record(Budget.objects.filter(user=request.user), month, year)
    report_query = urlencode({"month": month, "year": year})

    if request.GET.get("download") == "csv":
        rows = [
            [expense.date, expense.title, expense.category, expense.payment_method, expense.description, money(expense.amount)]
            for expense in expenses
        ]
        return csv_response(
            f"my-reports-{year}-{month:02d}.csv",
            ["Date", "Title", "Category", "Payment Method", "Description", "Amount"],
            rows,
        )

    if request.GET.get("download") == "pdf":
        pdf = build_statement_pdf(
            title="Personal Expense Statement",
            subtitle=f"Bank-style monthly statement for {calendar.month_name[month]} {year}",
            details=[
                ("Account holder", request.user.username),
                ("Email", request.user.email or "-"),
                ("Statement period", f"{calendar.month_name[month]} {year}"),
                ("Highest category", highest_category["label"] if highest_category else "None"),
                ("Budget source", monthly_record_source_label(budget, month, year)),
                ("Records", expenses.count()),
            ],
            summary_cards=budget_cards(total, budget),
            charts=[
                chart_from_summary("Category-wise Expense", categories, color=TEAL),
                chart_from_summary("Daily Expense Movement", daily, chart_type="line", color=CORAL),
            ],
            table_title="Transaction Statement",
            table_headers=["Date", "Title", "Category", "Payment", "Note", "Amount"],
            table_rows=expense_statement_rows(expenses),
            table_widths=[58, 102, 76, 70, 150, 72],
        )
        return pdf_response(f"my-reports-{year}-{month:02d}.pdf", pdf)

    context = {
        "form": form,
        "selected_month": calendar.month_name[month],
        "selected_year": year,
        "total": total,
        "category_summary": categories,
        "daily_summary": daily,
        "highest_category": highest_category,
        "budget": budget,
        "expenses": expenses,
        "report_query": report_query,
        "category_chart": chart_payload([row["label"] for row in categories], [row["value"] for row in categories]),
        "daily_chart": chart_payload([row["label"] for row in daily], [row["value"] for row in daily]),
    }
    return render(request, "expenses/monthly_report.html", context)


@login_required
def budget_setup(request):
    today = datetime.date.today()
    current_budget = effective_monthly_record(Budget.objects.filter(user=request.user), today.month, today.year)

    if request.method == "POST":
        form = BudgetForm(request.POST)
        if form.is_valid():
            month = int(form.cleaned_data["month"])
            year = int(form.cleaned_data["year"])
            amount = form.cleaned_data["amount"]
            Budget.objects.update_or_create(
                user=request.user,
                month=month,
                year=year,
                defaults={"amount": amount},
            )
            messages.success(request, "Budget saved successfully. It will carry forward until you change it.")
            return redirect("dashboard")
        messages.error(request, "Please correct the highlighted budget fields.")
    else:
        initial = {"month": today.month, "year": today.year}
        if current_budget:
            initial["amount"] = current_budget.amount
        form = BudgetForm(initial=initial)

    return render(
        request,
        "expenses/budget_form.html",
        {
            "form": form,
            "budget_source_label": monthly_record_source_label(current_budget, today.month, today.year),
        },
    )


@login_required
def family_group(request):
    create_form = FamilyGroupForm()
    join_form = JoinFamilyForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            create_form = FamilyGroupForm(request.POST)
            if create_form.is_valid():
                group = create_form.save(commit=False)
                group.created_by = request.user
                group.save()
                FamilyMembership.objects.get_or_create(user=request.user, family_group=group)
                messages.success(request, "Family group created successfully.")
                return redirect("family_group")
            messages.error(request, "Please correct the family group name.")
        elif action == "join":
            join_form = JoinFamilyForm(request.POST)
            if join_form.is_valid():
                code = join_form.cleaned_data["code"]
                group = FamilyGroup.objects.filter(code=code).first()
                if not group:
                    messages.error(request, "No family group found with that code.")
                else:
                    membership, created = FamilyMembership.objects.get_or_create(
                        user=request.user,
                        family_group=group,
                    )
                    if created:
                        messages.success(request, "Family joined successfully.")
                    else:
                        messages.info(request, "You are already a member of this family group.")
                    return redirect("family_group")
            else:
                messages.error(request, "Please enter a valid family code.")

    memberships = (
        FamilyMembership.objects.filter(user=request.user)
        .select_related("family_group")
        .prefetch_related("family_group__memberships__user")
    )
    return render(
        request,
        "expenses/family_group.html",
        {
            "create_form": create_form,
            "join_form": join_form,
            "memberships": memberships,
        },
    )


@login_required
def family_report(request):
    memberships = FamilyMembership.objects.filter(user=request.user).select_related("family_group")
    family_groups = [membership.family_group for membership in memberships]
    if not family_groups:
        messages.info(request, "Create or join a family group before viewing family.")
        return redirect("family_group")

    selected_group = family_groups[0]
    requested_group_id = request.POST.get("family_group") or request.GET.get("family_group")
    if requested_group_id:
        selected_group = get_object_or_404(FamilyGroup, pk=requested_group_id)
        if not FamilyMembership.objects.filter(user=request.user, family_group=selected_group).exists():
            return HttpResponseForbidden("You are not a member of this family group.")

    family_budget_form = None
    if request.method == "POST" and request.POST.get("action") == "set_family_budget":
        if not can_manage_family_group(request.user, selected_group):
            return HttpResponseForbidden("Only the family group creator can set the family budget.")
        family_budget_form = FamilyBudgetForm(request.POST)
        if family_budget_form.is_valid():
            budget_month = int(family_budget_form.cleaned_data["month"])
            budget_year = int(family_budget_form.cleaned_data["year"])
            FamilyBudget.objects.update_or_create(
                family_group=selected_group,
                month=budget_month,
                year=budget_year,
                defaults={"amount": family_budget_form.cleaned_data["amount"]},
            )
            messages.success(request, "Family budget saved successfully. It will carry forward until the creator changes it.")
            query = urlencode({"family_group": selected_group.pk, "month": budget_month, "year": budget_year})
            return redirect(f"{reverse('family_report')}?{query}")
        messages.error(request, "Please correct the highlighted family budget fields.")

    form = ReportFilterForm(request.GET or None)
    today = datetime.date.today()
    month = today.month
    year = today.year
    if form.is_valid():
        month = int(form.cleaned_data["month"])
        year = int(form.cleaned_data["year"])

    member_ids = list(
        FamilyMembership.objects.filter(family_group=selected_group).values_list("user_id", flat=True)
    )
    members = selected_group.memberships.select_related("user")
    family_expenses = Expense.objects.filter(user_id__in=member_ids).select_related("user")
    expenses = family_expenses.filter(date__month=month, date__year=year)
    member_rows = (
        expenses.values("user__username")
        .annotate(total=Sum("amount"))
        .order_by("-total", "user__username")
    )
    member_summary = [
        {
            "label": row["user__username"],
            "total": row["total"],
            "value": decimal_to_float(row["total"]),
        }
        for row in member_rows
    ]
    categories = category_summary(expenses)
    daily = daily_summary(expenses)
    total = sum_amount(expenses)
    family_budget = effective_monthly_record(FamilyBudget.objects.filter(family_group=selected_group), month, year)
    family_remaining_budget = family_budget.amount - total if family_budget else None
    family_budget_initial = {"month": month, "year": year}
    if family_budget:
        family_budget_initial["amount"] = family_budget.amount
    if family_budget_form is None:
        family_budget_form = FamilyBudgetForm(initial=family_budget_initial)

    default_date_from, default_date_to = month_date_range(year, month)
    has_transaction_filter = any(key.startswith("tx-") for key in request.GET)
    transaction_form = FamilyTransactionFilterForm(
        request.GET if has_transaction_filter else None,
        members=members,
        prefix="tx",
        initial={"date_from": default_date_from, "date_to": default_date_to},
    )
    transaction_expenses = family_expenses
    transaction_title = ""
    transaction_member = ""
    transaction_category = ""
    transaction_payment_method = ""
    transaction_date_from = default_date_from
    transaction_date_to = default_date_to

    if transaction_form.is_valid():
        transaction_title = transaction_form.cleaned_data.get("title") or ""
        transaction_member = transaction_form.cleaned_data.get("member") or ""
        transaction_category = transaction_form.cleaned_data.get("category") or ""
        transaction_payment_method = transaction_form.cleaned_data.get("payment_method") or ""
        transaction_date_from = transaction_form.cleaned_data.get("date_from") or default_date_from
        transaction_date_to = transaction_form.cleaned_data.get("date_to") or default_date_to

        if transaction_title:
            transaction_expenses = transaction_expenses.filter(title__icontains=transaction_title)
        if transaction_member:
            transaction_expenses = transaction_expenses.filter(user_id=transaction_member)
        if transaction_category:
            transaction_expenses = transaction_expenses.filter(category=transaction_category)
        if transaction_payment_method:
            transaction_expenses = transaction_expenses.filter(payment_method=transaction_payment_method)
        if transaction_date_from:
            transaction_expenses = transaction_expenses.filter(date__gte=transaction_date_from)
        if transaction_date_to:
            transaction_expenses = transaction_expenses.filter(date__lte=transaction_date_to)
    else:
        transaction_expenses = transaction_expenses.filter(
            date__gte=transaction_date_from,
            date__lte=transaction_date_to,
        )

    transaction_total = sum_amount(transaction_expenses)
    report_query = urlencode({"family_group": selected_group.pk, "month": month, "year": year})
    transaction_query_data = {
        "family_group": selected_group.pk,
        "month": month,
        "year": year,
        "tx-date_from": transaction_date_from.isoformat() if transaction_date_from else "",
        "tx-date_to": transaction_date_to.isoformat() if transaction_date_to else "",
    }
    if transaction_title:
        transaction_query_data["tx-title"] = transaction_title
    if transaction_member:
        transaction_query_data["tx-member"] = transaction_member
    if transaction_category:
        transaction_query_data["tx-category"] = transaction_category
    if transaction_payment_method:
        transaction_query_data["tx-payment_method"] = transaction_payment_method
    transaction_query = urlencode(transaction_query_data)

    if request.GET.get("download") == "csv":
        rows = [
            [
                expense.date,
                expense.user.username,
                expense.title,
                expense.category,
                expense.payment_method,
                expense.description,
                money(expense.amount),
            ]
            for expense in expenses
        ]
        return csv_response(
            f"family-statement-{selected_group.pk}-{year}-{month:02d}.csv",
            ["Date", "Member", "Title", "Category", "Payment Method", "Description", "Amount"],
            rows,
        )

    if request.GET.get("download") == "pdf":
        pdf = build_statement_pdf(
            title="Family Expense Statement",
            subtitle=f"Bank-style family statement for {calendar.month_name[month]} {year}",
            details=[
                ("Family group", selected_group.name),
                ("Creator", selected_group.created_by.username),
                ("Statement period", f"{calendar.month_name[month]} {year}"),
                ("Members", members.count()),
                ("Budget source", monthly_record_source_label(family_budget, month, year)),
                ("Records", expenses.count()),
            ],
            summary_cards=budget_cards(total, family_budget, "Family Budget"),
            charts=[
                chart_from_summary("Member-wise Expense", member_summary, color=NAVY),
                chart_from_summary("Category-wise Family Expense", categories, color=TEAL),
                chart_from_summary("Daily Family Expense Movement", daily, chart_type="line", color=CORAL),
            ],
            table_title="Family Transaction Statement",
            table_headers=["Date", "Member", "Title", "Category", "Payment", "Note", "Amount"],
            table_rows=expense_statement_rows(expenses, include_member=True),
            table_widths=[54, 62, 88, 66, 62, 142, 54],
        )
        return pdf_response(f"family-statement-{selected_group.pk}-{year}-{month:02d}.pdf", pdf)

    if request.GET.get("download") == "transactions_csv":
        rows = [
            [
                expense.date,
                expense.user.username,
                expense.title,
                expense.category,
                expense.payment_method,
                expense.description,
                money(expense.amount),
            ]
            for expense in transaction_expenses
        ]
        return csv_response(
            f"family-transactions-{selected_group.pk}-{transaction_date_from}-{transaction_date_to}.csv",
            ["Date", "Member", "Title", "Category", "Payment Method", "Description", "Amount"],
            rows,
        )

    if request.GET.get("download") == "transactions_pdf":
        transaction_categories = category_summary(transaction_expenses)
        transaction_daily = daily_summary(transaction_expenses)
        transaction_members = [
            {
                "label": row["user__username"],
                "total": row["total"],
                "value": decimal_to_float(row["total"]),
            }
            for row in (
                transaction_expenses.values("user__username")
                .annotate(total=Sum("amount"))
                .order_by("-total", "user__username")
            )
        ]
        pdf = build_statement_pdf(
            title="Family Transaction Statement",
            subtitle=f"Custom date statement from {transaction_date_from} to {transaction_date_to}",
            details=[
                ("Family group", selected_group.name),
                ("Creator", selected_group.created_by.username),
                ("Date range", f"{transaction_date_from} to {transaction_date_to}"),
                ("Selected budget month", f"{calendar.month_name[month]} {year}"),
                ("Budget source", monthly_record_source_label(family_budget, month, year)),
                ("Records", transaction_expenses.count()),
            ],
            summary_cards=budget_cards(transaction_total, family_budget, "Family Budget"),
            charts=[
                chart_from_summary("Filtered Member-wise Expense", transaction_members, color=NAVY),
                chart_from_summary("Filtered Category-wise Expense", transaction_categories, color=TEAL),
                chart_from_summary("Filtered Daily Expense Movement", transaction_daily, chart_type="line", color=CORAL),
            ],
            table_title="Filtered Family Transactions",
            table_headers=["Date", "Member", "Title", "Category", "Payment", "Note", "Amount"],
            table_rows=expense_statement_rows(transaction_expenses, include_member=True),
            table_widths=[54, 62, 88, 66, 62, 142, 54],
        )
        return pdf_response(
            f"family-transactions-{selected_group.pk}-{transaction_date_from}-{transaction_date_to}.pdf",
            pdf,
        )

    context = {
        "form": form,
        "family_groups": family_groups,
        "selected_group": selected_group,
        "selected_month": calendar.month_name[month],
        "selected_month_number": month,
        "selected_year": year,
        "members": members,
        "total": total,
        "family_budget": family_budget,
        "family_budget_source_label": monthly_record_source_label(family_budget, month, year),
        "family_budget_form": family_budget_form,
        "family_remaining_budget": family_remaining_budget,
        "family_remaining_budget_negative": family_remaining_budget is not None and family_remaining_budget < 0,
        "family_budget_alerts": budget_alerts(family_budget, total, "Family budget"),
        "family_budget_mood": budget_mood(family_budget, total),
        "is_group_creator": can_manage_family_group(request.user, selected_group),
        "member_summary": member_summary,
        "category_summary": categories,
        "daily_summary": daily,
        "expenses": expenses,
        "transaction_form": transaction_form,
        "transaction_expenses": transaction_expenses,
        "transaction_total": transaction_total,
        "transaction_date_from": transaction_date_from,
        "transaction_date_to": transaction_date_to,
        "report_query": report_query,
        "transaction_query": transaction_query,
        "member_chart": chart_payload([row["label"] for row in member_summary], [row["value"] for row in member_summary]),
        "category_chart": chart_payload([row["label"] for row in categories], [row["value"] for row in categories]),
        "daily_chart": chart_payload([row["label"] for row in daily], [row["value"] for row in daily]),
    }
    return render(request, "expenses/family_report.html", context)


@login_required
def profile(request):
    expenses = Expense.objects.filter(user=request.user)
    today = datetime.date.today()
    current_month = expenses.filter(date__year=today.year, date__month=today.month)
    context = {
        "total_expenses": sum_amount(expenses),
        "current_month_total": sum_amount(current_month),
        "expense_count": expenses.count(),
        "family_count": FamilyMembership.objects.filter(user=request.user).count(),
        "budget_count": Budget.objects.filter(user=request.user).count(),
    }
    return render(request, "expenses/profile.html", context)
