import datetime

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Budget, Expense, FamilyBudget, FamilyGroup, SECURITY_QUESTION


CURRENT_YEAR = datetime.date.today().year
YEAR_CHOICES = [(year, year) for year in range(CURRENT_YEAR - 5, CURRENT_YEAR + 6)]
MONTH_CHOICES = [
    (1, "January"),
    (2, "February"),
    (3, "March"),
    (4, "April"),
    (5, "May"),
    (6, "June"),
    (7, "July"),
    (8, "August"),
    (9, "September"),
    (10, "October"),
    (11, "November"),
    (12, "December"),
]


def apply_bootstrap_widgets(fields):
    for field in fields.values():
        css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
        existing = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    security_answer = forms.CharField(
        label=SECURITY_QUESTION,
        max_length=120,
        help_text="This answer is used if you forget your password.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["username"].widget.attrs.update({"placeholder": "Choose a username"})
        self.fields["email"].widget.attrs.update({"placeholder": "you@example.com"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Create a password"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm password"})
        self.fields["security_answer"].widget.attrs.update({"placeholder": "Example: Kathmandu"})

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_security_answer(self):
        answer = self.cleaned_data["security_answer"].strip()
        if not answer:
            raise forms.ValidationError("Please enter your security answer.")
        return answer


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["username"].label = "User ID or Username"
        self.fields["username"].help_text = "Use the numeric User ID from your profile or your username."
        self.fields["username"].widget.attrs.update({"placeholder": "Example: 12 or alex"})
        self.fields["password"].widget.attrs.update({"placeholder": "Password"})

    def clean(self):
        login_identifier = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if login_identifier is not None and password:
            username = self.resolve_login_username(login_identifier)
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None and username != login_identifier:
                self.user_cache = authenticate(self.request, username=login_identifier, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def resolve_login_username(self, login_identifier):
        identifier = str(login_identifier).strip()
        if identifier.isdigit():
            user = User.objects.filter(pk=int(identifier)).first()
            if user:
                return user.get_username()
        return identifier


class PasswordResetEmailForm(forms.Form):
    email = forms.EmailField(label="Gmail / Email address")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["email"].widget.attrs.update({"placeholder": "you@example.com"})

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class SecurityAnswerForm(forms.Form):
    answer = forms.CharField(label=SECURITY_QUESTION, max_length=120)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["answer"].widget.attrs.update({"placeholder": "Enter your dream place"})


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["new_password1"].widget.attrs.update({"placeholder": "Create a new password"})
        self.fields["new_password2"].widget.attrs.update({"placeholder": "Confirm new password"})


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ("title", "amount", "category", "date", "payment_method", "description")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["title"].widget.attrs.update({"placeholder": "Example: Groceries"})
        self.fields["amount"].widget.attrs.update({"min": "0.01", "step": "0.01"})
        self.fields["description"].widget.attrs.update({"placeholder": "Optional note"})


class ExpenseSearchForm(forms.Form):
    title = forms.CharField(required=False, label="Search title")
    category = forms.ChoiceField(
        required=False,
        choices=[("", "All categories"), *Expense.CATEGORY_CHOICES],
    )
    payment_method = forms.ChoiceField(
        required=False,
        choices=[("", "All methods"), *Expense.PAYMENT_METHOD_CHOICES],
    )
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_from = forms.DateField(required=False, label="From", widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, label="To", widget=forms.DateInput(attrs={"type": "date"}))
    month = forms.ChoiceField(required=False, choices=[("", "Any month"), *MONTH_CHOICES])
    year = forms.ChoiceField(required=False, choices=[("", "Any year"), *YEAR_CHOICES])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)


class ReportFilterForm(forms.Form):
    month = forms.ChoiceField(choices=MONTH_CHOICES)
    year = forms.ChoiceField(choices=YEAR_CHOICES)

    def __init__(self, *args, **kwargs):
        initial = kwargs.setdefault("initial", {})
        today = datetime.date.today()
        initial.setdefault("month", today.month)
        initial.setdefault("year", today.year)
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)


class BudgetForm(forms.ModelForm):
    month = forms.ChoiceField(choices=MONTH_CHOICES)
    year = forms.ChoiceField(choices=YEAR_CHOICES)

    class Meta:
        model = Budget
        fields = ("month", "year", "amount")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["amount"].widget.attrs.update({"min": "0.01", "step": "0.01"})


class FamilyBudgetForm(forms.ModelForm):
    month = forms.ChoiceField(choices=MONTH_CHOICES)
    year = forms.ChoiceField(choices=YEAR_CHOICES)

    class Meta:
        model = FamilyBudget
        fields = ("month", "year", "amount")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["amount"].widget.attrs.update({"min": "0.01", "step": "0.01"})


class FamilyTransactionFilterForm(forms.Form):
    title = forms.CharField(required=False, label="Search title")
    member = forms.ChoiceField(required=False, choices=[("", "All members")])
    category = forms.ChoiceField(
        required=False,
        choices=[("", "All categories"), *Expense.CATEGORY_CHOICES],
    )
    payment_method = forms.ChoiceField(
        required=False,
        choices=[("", "All methods"), *Expense.PAYMENT_METHOD_CHOICES],
    )
    date_from = forms.DateField(required=False, label="From", widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, label="To", widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, members=None, **kwargs):
        super().__init__(*args, **kwargs)
        if members is not None:
            self.fields["member"].choices = [
                ("", "All members"),
                *[(member.user_id, member.user.username) for member in members],
            ]
        apply_bootstrap_widgets(self.fields)


class FamilyGroupForm(forms.ModelForm):
    class Meta:
        model = FamilyGroup
        fields = ("name",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["name"].widget.attrs.update({"placeholder": "Example: Sharma Family"})


class JoinFamilyForm(forms.Form):
    code = forms.CharField(max_length=12)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
        self.fields["code"].widget.attrs.update({"placeholder": "Family code"})

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()
