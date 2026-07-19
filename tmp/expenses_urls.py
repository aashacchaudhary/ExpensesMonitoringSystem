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
    path("reports/monthly/", views.monthly_report, name="monthly_report"),
    path("budget/", views.budget_setup, name="budget_setup"),
    path("family/", views.family_group, name="family_group"),
    path("family/report/", views.family_report, name="family_report"),
    path("profile/", views.profile, name="profile"),
]
