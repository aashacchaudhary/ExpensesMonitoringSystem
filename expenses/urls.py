from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.ExpenseLoginView.as_view(), name="login"),
    path("password-reset/", views.password_reset_email, name="password_reset_email"),
    path("password-reset/security/", views.password_reset_security, name="password_reset_security"),
    path("password-reset/confirm/", views.password_reset_confirm, name="password_reset_confirm"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("expenses/add/", views.expense_create, name="expense_create"),
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/<int:pk>/delete/", views.expense_delete, name="expense_delete"),
    path("recurring/", views.recurring_list, name="recurring_list"),
    path("recurring/create/", views.recurring_create, name="recurring_create"),
    path("recurring/<int:pk>/edit/", views.recurring_edit, name="recurring_edit"),
    path("recurring/<int:pk>/delete/", views.recurring_delete, name="recurring_delete"),
    path("reports/monthly/", views.monthly_report, name="monthly_report"),
    path("emi/", views.emi_calculator, name="emi_calculator"),
    path("emi/export/", views.emi_export, name="emi_export"),
    path("savings/", views.savings_goal, name="savings_goal"),
    path("budget/", views.budget_setup, name="budget_setup"),
    path("family/", views.family_group, name="family_group"),
    path("family/report/", views.family_report, name="family_report"),
    path("profile/", views.profile, name="profile"),
    path("preferences/", views.email_preferences, name="email_preferences"),
    

]
