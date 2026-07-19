import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Budget, Expense, FamilyBudget, FamilyGroup, FamilyMembership, UserSecurityAnswer


class ExpenseManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alex",
            email="alex@example.com",
            password="StrongPass123",
        )
        self.other = User.objects.create_user(
            username="sam",
            email="sam@example.com",
            password="StrongPass123",
        )

    def previous_month(self, date_value):
        if date_value.month == 1:
            return 12, date_value.year - 1
        return date_value.month - 1, date_value.year

    def test_register_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "alex@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "security_answer": "Kathmandu",
            },
        )
        self.assertContains(response, "An account with this email already exists.")

    def test_register_stores_security_answer(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "dreamer",
                "email": "dreamer@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "security_answer": "Pokhara",
            },
        )
        user = User.objects.get(username="dreamer")
        profile = UserSecurityAnswer.objects.get(user=user)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(profile.check_answer("pokhara"))
        self.assertFalse(profile.check_answer("Kathmandu"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_login_accepts_numeric_user_id(self):
        response = self.client.post(
            reverse("login"),
            {"username": str(self.user.pk), "password": "StrongPass123"},
            follow=True,
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_still_accepts_username(self):
        response = self.client.post(
            reverse("login"),
            {"username": "alex", "password": "StrongPass123"},
            follow=True,
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_password_reset_uses_default_answer_for_existing_account(self):
        self.assertFalse(UserSecurityAnswer.objects.filter(user=self.user).exists())

        email_response = self.client.post(
            reverse("password_reset_email"),
            {"email": "alex@example.com"},
            follow=True,
        )
        wrong_answer_response = self.client.post(
            reverse("password_reset_security"),
            {"answer": "Paris"},
        )
        answer_response = self.client.post(
            reverse("password_reset_security"),
            {"answer": "Kathmandu"},
            follow=True,
        )
        confirm_response = self.client.post(
            reverse("password_reset_confirm"),
            {
                "new_password1": "NewStrongPass456",
                "new_password2": "NewStrongPass456",
            },
            follow=True,
        )

        self.assertContains(email_response, "What is your dream place ?")
        self.assertContains(wrong_answer_response, "Security answer did not match.")
        self.assertContains(answer_response, "Change password")
        self.assertRedirects(confirm_response, reverse("login"))
        self.assertTrue(self.client.login(username="alex", password="NewStrongPass456"))

    def test_password_reset_uses_signup_security_answer(self):
        profile = UserSecurityAnswer(user=self.user)
        profile.set_answer("London")
        profile.save()

        self.client.post(reverse("password_reset_email"), {"email": "alex@example.com"})
        wrong_response = self.client.post(reverse("password_reset_security"), {"answer": "Kathmandu"})
        right_response = self.client.post(reverse("password_reset_security"), {"answer": "London"}, follow=True)

        self.assertContains(wrong_response, "Security answer did not match.")
        self.assertContains(right_response, "Change password")

    def test_user_only_sees_own_expenses(self):
        Expense.objects.create(
            user=self.user,
            title="Lunch",
            amount=Decimal("12.50"),
            category="Food",
            date=datetime.date.today(),
            payment_method="Cash",
        )
        Expense.objects.create(
            user=self.other,
            title="Private rent",
            amount=Decimal("900.00"),
            category="Rent",
            date=datetime.date.today(),
            payment_method="Bank",
        )

        self.client.login(username="alex", password="StrongPass123")
        response = self.client.get(reverse("expense_list"))

        self.assertContains(response, "Lunch")
        self.assertNotContains(response, "Private rent")

    def test_budget_remaining_appears_on_dashboard(self):
        today = datetime.date.today()
        Budget.objects.create(user=self.user, month=today.month, year=today.year, amount=Decimal("100.00"))
        Expense.objects.create(
            user=self.user,
            title="Medicine",
            amount=Decimal("25.00"),
            category="Health",
            date=today,
            payment_method="Card",
        )

        self.client.login(username="alex", password="StrongPass123")
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "75.00")

    def test_personal_budget_carries_forward_until_changed(self):
        today = datetime.date.today()
        previous_month, previous_year = self.previous_month(today)
        Budget.objects.create(user=self.user, month=previous_month, year=previous_year, amount=Decimal("100.00"))
        Expense.objects.create(
            user=self.user,
            title="Current month groceries",
            amount=Decimal("25.00"),
            category="Food",
            date=today,
            payment_method="Cash",
        )

        self.client.login(username="alex", password="StrongPass123")
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "75.00")
        self.assertContains(response, "Carried forward from")

    def test_family_report_includes_members_but_not_outsiders(self):
        today = datetime.date.today()
        outside = User.objects.create_user(
            username="outside",
            email="outside@example.com",
            password="StrongPass123",
        )
        group = FamilyGroup.objects.create(name="Family", created_by=self.user)
        FamilyMembership.objects.create(user=self.user, family_group=group)
        FamilyMembership.objects.create(user=self.other, family_group=group)

        Expense.objects.create(
            user=self.user,
            title="Groceries",
            amount=Decimal("30.00"),
            category="Food",
            date=today,
            payment_method="Cash",
        )
        Expense.objects.create(
            user=self.other,
            title="School books",
            amount=Decimal("45.00"),
            category="Education",
            date=today,
            payment_method="Card",
        )
        Expense.objects.create(
            user=outside,
            title="Outside bill",
            amount=Decimal("999.00"),
            category="Bills",
            date=today,
            payment_method="Bank",
        )

        self.client.login(username="alex", password="StrongPass123")
        response = self.client.get(
            reverse("family_report"),
            {"family_group": group.pk, "month": today.month, "year": today.year},
        )

        self.assertContains(response, "75.00")
        self.assertContains(response, "Groceries")
        self.assertContains(response, "School books")
        self.assertNotContains(response, "Outside bill")

    def test_authenticated_pages_render(self):
        today = datetime.date.today()
        group = FamilyGroup.objects.create(name="Render Family", created_by=self.user)
        FamilyMembership.objects.create(user=self.user, family_group=group)
        Budget.objects.create(user=self.user, month=today.month, year=today.year, amount=Decimal("500.00"))

        self.client.login(username="alex", password="StrongPass123")

        urls = [
            reverse("dashboard"),
            reverse("expense_create"),
            reverse("expense_list"),
            reverse("monthly_report"),
            reverse("budget_setup"),
            reverse("family_group"),
            reverse("profile"),
            f"{reverse('family_report')}?family_group={group.pk}&month={today.month}&year={today.year}",
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_expense_list_filters_custom_date_range(self):
        Expense.objects.create(
            user=self.user,
            title="Inside range",
            amount=Decimal("20.00"),
            category="Food",
            date=datetime.date(2026, 5, 3),
            payment_method="Cash",
        )
        Expense.objects.create(
            user=self.user,
            title="Outside range",
            amount=Decimal("30.00"),
            category="Bills",
            date=datetime.date(2026, 4, 25),
            payment_method="Bank",
        )

        self.client.login(username="alex", password="StrongPass123")
        response = self.client.get(
            reverse("expense_list"),
            {"date_from": "2026-05-01", "date_to": "2026-05-31"},
        )

        self.assertContains(response, "Inside range")
        self.assertNotContains(response, "Outside range")

    def test_my_reports_download_csv_and_pdf(self):
        Expense.objects.create(
            user=self.user,
            title="Report lunch",
            amount=Decimal("15.00"),
            category="Food",
            date=datetime.date(2026, 5, 5),
            payment_method="Cash",
        )

        self.client.login(username="alex", password="StrongPass123")
        csv_response = self.client.get(reverse("monthly_report"), {"month": 5, "year": 2026, "download": "csv"})
        pdf_response = self.client.get(reverse("monthly_report"), {"month": 5, "year": 2026, "download": "pdf"})

        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv")
        self.assertIn("attachment;", csv_response["Content-Disposition"])
        self.assertContains(csv_response, "Report lunch")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))

    def test_family_reports_download_csv_and_pdf(self):
        group = FamilyGroup.objects.create(name="Download Family", created_by=self.user)
        FamilyMembership.objects.create(user=self.user, family_group=group)
        Expense.objects.create(
            user=self.user,
            title="Family dinner",
            amount=Decimal("40.00"),
            category="Family",
            date=datetime.date(2026, 5, 8),
            payment_method="Card",
        )

        self.client.login(username="alex", password="StrongPass123")
        csv_response = self.client.get(
            reverse("family_report"),
            {"family_group": group.pk, "month": 5, "year": 2026, "download": "csv"},
        )
        pdf_response = self.client.get(
            reverse("family_report"),
            {"family_group": group.pk, "month": 5, "year": 2026, "download": "pdf"},
        )

        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv")
        self.assertContains(csv_response, "Family dinner")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))

    def test_family_budget_can_only_be_set_by_group_creator(self):
        group = FamilyGroup.objects.create(name="Budget Family", created_by=self.user)
        FamilyMembership.objects.create(user=self.user, family_group=group)
        FamilyMembership.objects.create(user=self.other, family_group=group)

        self.client.login(username="sam", password="StrongPass123")
        forbidden_response = self.client.post(
            reverse("family_report"),
            {
                "action": "set_family_budget",
                "family_group": group.pk,
                "month": 5,
                "year": 2026,
                "amount": "700.00",
            },
        )
        self.assertEqual(forbidden_response.status_code, 403)
        self.assertFalse(FamilyBudget.objects.filter(family_group=group).exists())

        self.client.logout()
        self.client.login(username="alex", password="StrongPass123")
        response = self.client.post(
            reverse("family_report"),
            {
                "action": "set_family_budget",
                "family_group": group.pk,
                "month": 5,
                "year": 2026,
                "amount": "700.00",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(FamilyBudget.objects.filter(family_group=group, month=5, year=2026, amount=Decimal("700.00")).exists())

    def test_family_budget_form_is_visible_to_group_creator(self):
        group = FamilyGroup.objects.create(name="Visible Budget Family", created_by=self.user)
        FamilyMembership.objects.create(user=self.user, family_group=group)

        self.client.login(username="alex", password="StrongPass123")
        response = self.client.get(reverse("family_report"), {"family_group": group.pk, "month": 5, "year": 2026})

        self.assertContains(response, "Save Family Budget")
        self.assertNotContains(response, "Ask alex to set or update")

    def test_family_budget_carries_forward_until_creator_changes_it(self):
        group = FamilyGroup.objects.create(name="Carry Family", created_by=self.user)
        FamilyMembership.objects.create(user=self.user, family_group=group)
        FamilyBudget.objects.create(family_group=group, month=5, year=2026, amount=Decimal("200.00"))
        Expense.objects.create(
            user=self.user,
            title="June family groceries",
            amount=Decimal("50.00"),
            category="Food",
            date=datetime.date(2026, 6, 8),
            payment_method="Cash",
        )

        self.client.login(username="alex", password="StrongPass123")
        response = self.client.get(
            reverse("family_report"),
            {"family_group": group.pk, "month": 6, "year": 2026},
        )

        self.assertContains(response, "150.00")
        self.assertContains(response, "Carried forward from May 2026")

    def test_family_transactions_filter_custom_date_range_and_download(self):
        group = FamilyGroup.objects.create(name="Transactions Family", created_by=self.user)
        outside_group = FamilyGroup.objects.create(name="Outside Family", created_by=self.other)
        FamilyMembership.objects.create(user=self.user, family_group=group)
        FamilyMembership.objects.create(user=self.other, family_group=outside_group)
        Expense.objects.create(
            user=self.user,
            title="Inside family range",
            amount=Decimal("20.00"),
            category="Food",
            date=datetime.date(2026, 5, 10),
            payment_method="Cash",
        )
        Expense.objects.create(
            user=self.user,
            title="Outside date range",
            amount=Decimal("30.00"),
            category="Bills",
            date=datetime.date(2026, 4, 20),
            payment_method="Bank",
        )
        Expense.objects.create(
            user=self.other,
            title="Different family private",
            amount=Decimal("999.00"),
            category="Shopping",
            date=datetime.date(2026, 5, 12),
            payment_method="Card",
        )

        self.client.login(username="alex", password="StrongPass123")
        params = {
            "family_group": group.pk,
            "month": 5,
            "year": 2026,
            "tx-date_from": "2026-05-01",
            "tx-date_to": "2026-05-31",
        }
        response = self.client.get(reverse("family_report"), params)
        csv_response = self.client.get(reverse("family_report"), {**params, "download": "transactions_csv"})
        pdf_response = self.client.get(reverse("family_report"), {**params, "download": "transactions_pdf"})

        self.assertContains(response, "Inside family range")
        self.assertNotContains(response, "Outside date range")
        self.assertNotContains(response, "Different family private")
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv")
        self.assertContains(csv_response, "Inside family range")
        self.assertNotContains(csv_response, "Outside date range")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))
