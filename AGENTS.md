# AGENTS.md — Expense Management System

## Project Overview

A Django 5.x monolithic web application for tracking personal expenses, monthly budgets, budget alerts, reports, and family-level expense summaries with Chart.js graphs and bank-style PDF statements. Uses SQLite, Django templates with Bootstrap 5, and has zero external Python dependencies beyond Django itself.

---

## Tech Stack

| Layer        | Technology                                   |
|-------------|----------------------------------------------|
| Backend     | Python 3, Django ≥5.0, <6.0                  |
| Database    | SQLite (`db.sqlite3` at project root)         |
| Auth        | Django built-in authentication (`django.contrib.auth`) |
| Frontend    | Django Templates, HTML5, CSS3, JavaScript     |
| UI          | Bootstrap 5 (CDN), Bootstrap Icons (CDN)      |
| Charts      | Chart.js (CDN)                                |
| PDFs        | Custom raw-PDF builder (`expenses/pdf_builder.py`) — no external PDF library |
| Time zone   | `Asia/Kathmandu` (`USE_TZ = True`)            |

Only dependency in `requirements.txt`: `Django>=5.0,<6.0`

---

## Directory Structure

```
ExpensesMonitoringSystem/
├── manage.py                       # Django management entry point
├── requirements.txt                # Single dependency: Django 5.x
├── db.sqlite3                      # SQLite database (dev data)
├── expense_manager/                # Django project package
│   ├── settings.py                 # Project settings (DEBUG=True, SQLite, Asia/Kathmandu TZ)
│   ├── urls.py                     # Root URL config → includes expenses.urls
│   ├── wsgi.py
│   └── asgi.py
├── expenses/                       # Main (and only) Django app
│   ├── models.py                   # 6 models (see Data Models below)
│   ├── views.py                    # All views (~937 lines) — function-based + 1 CBV
│   ├── forms.py                    # 13 form classes with Bootstrap widget styling
│   ├── urls.py                     # 14 URL patterns
│   ├── admin.py                    # Admin registrations for all 6 models
│   ├── pdf_builder.py              # Raw PDF generator (no third-party library)
│   ├── tests.py                    # 19 test methods in 1 TestCase class
│   ├── templates/expenses/         # 15 Django templates
│   │   ├── base.html               # Base template (Bootstrap 5 CDN, Chart.js CDN)
│   │   ├── home.html               # Landing page (redirects authenticated users)
│   │   ├── login.html              # Login (User ID or username)
│   │   ├── register.html           # Registration with security question
│   │   ├── password_reset_*.html   # 3 password reset step templates
│   │   ├── dashboard.html          # Main dashboard with charts and budget mood ring
│   │   ├── expense_form.html       # Add expense form
│   │   ├── expense_list.html       # Expense listing with search/filter
│   │   ├── budget_form.html        # Personal budget setup
│   │   ├── monthly_report.html     # Monthly report with CSV/PDF download
│   │   ├── family_group.html       # Create/join family groups
│   │   ├── family_report.html      # Family report with transaction filtering
│   │   └── profile.html            # User profile summary
│   └── static/expenses/
│       ├── css/styles.css          # Custom CSS (~20KB, soft dashboard cards)
│       └── js/charts.js            # Chart.js initialization helpers
├── Documentation/                  # Auto-generated docs, diagrams, PDF report
└── doc-overleaf/                   # Overleaf/LaTeX documentation files
```

---

## Data Models

All models are in `expenses/models.py`. There are 6 models:

### UserSecurityAnswer
- **Purpose**: Stores hashed security answer for password recovery
- **Fields**: `user` (OneToOne → User), `question`, `answer_hash`, `created_at`, `updated_at`
- **Key behavior**: Uses `make_password` / `check_password` for answer hashing; answers are normalized (lowered, whitespace-collapsed) before hashing
- **Default security question**: `"What is your dream place ?"`
- **Default answer for pre-existing accounts**: `"Kathmandu"`

### Expense
- **Purpose**: Individual expense record
- **Fields**: `user` (FK → User), `title`, `amount` (Decimal, min 0.01), `category`, `date`, `payment_method`, `description`, `created_at`, `updated_at`
- **Categories**: Food, Transport, Rent, Education, Health, Shopping, Entertainment, Bills, Family, Other
- **Payment methods**: Cash, Bank, Card, Online Wallet, Other
- **Ordering**: `-date`, `-created_at`

### Budget
- **Purpose**: Per-user monthly budget
- **Fields**: `user` (FK → User), `month`, `year`, `amount` (Decimal, min 0.01), `created_at`, `updated_at`
- **Constraint**: `UniqueConstraint(fields=["user", "month", "year"])`
- **Key behavior**: Budgets **carry forward** — if no budget is set for a given month, the most recent prior budget is used (see `effective_monthly_record()` in views)

### FamilyGroup
- **Purpose**: Family expense-sharing group
- **Fields**: `name`, `code` (auto-generated 8-char uppercase alphanumeric, unique), `created_by` (FK → User), `created_at`
- **Key behavior**: `code` is generated on save if empty via `generate_unique_code()`

### FamilyBudget
- **Purpose**: Monthly budget for a family group (separate from personal budget)
- **Fields**: `family_group` (FK → FamilyGroup), `month`, `year`, `amount`, `created_at`, `updated_at`
- **Constraint**: `UniqueConstraint(fields=["family_group", "month", "year"])`
- **Access control**: Only the group **creator** can set/update the family budget

### FamilyMembership
- **Purpose**: Join table linking users to family groups
- **Fields**: `user` (FK → User), `family_group` (FK → FamilyGroup), `joined_at`
- **Constraint**: `UniqueConstraint(fields=["user", "family_group"])`

---

## URL Routes

All routes are under `expenses/urls.py`, included at the root (`""`) from `expense_manager/urls.py`:

| URL Pattern                          | View                         | Name                       | Auth Required |
|--------------------------------------|------------------------------|----------------------------|:---:|
| `/`                                  | `home`                       | `home`                     | No  |
| `/register/`                         | `register`                   | `register`                 | No  |
| `/login/`                            | `ExpenseLoginView` (CBV)     | `login`                    | No  |
| `/password-reset/`                   | `password_reset_email`       | `password_reset_email`     | No  |
| `/password-reset/security/`          | `password_reset_security`    | `password_reset_security`  | No  |
| `/password-reset/confirm/`           | `password_reset_confirm`     | `password_reset_confirm`   | No  |
| `/logout/`                           | `LogoutView` (Django built-in)| `logout`                  | No  |
| `/dashboard/`                        | `dashboard`                  | `dashboard`                | Yes |
| `/expenses/add/`                     | `expense_create`             | `expense_create`           | Yes |
| `/expenses/`                         | `expense_list`               | `expense_list`             | Yes |
| `/expenses/<int:pk>/delete/`         | `expense_delete` (POST-only) | `expense_delete`           | Yes |
| `/reports/monthly/`                  | `monthly_report`             | `monthly_report`           | Yes |
| `/budget/`                           | `budget_setup`               | `budget_setup`             | Yes |
| `/family/`                           | `family_group`               | `family_group`             | Yes |
| `/family/report/`                    | `family_report`              | `family_report`            | Yes |
| `/profile/`                          | `profile`                    | `profile`                  | Yes |

**Admin panel**: `/admin/` (standard Django admin)

---

## Views Architecture

All views are in `expenses/views.py`. Style is **function-based views** with one CBV (`ExpenseLoginView`).

### Important Helper Functions (used across views)
- `decimal_to_float()` — safe Decimal → float conversion for JSON/Chart.js
- `sum_amount(queryset)` — aggregate `Sum("amount")` with zero fallback
- `category_summary(queryset)` — returns `[{label, total, value}]` grouped by category
- `daily_summary(queryset)` — returns `[{label, date, total, value}]` grouped by date
- `monthly_summary_for_year(queryset, year)` — returns 12-month totals for yearly charts
- `effective_monthly_record(queryset, month, year)` — **carry-forward budget logic**: finds the most recent budget ≤ the given month/year
- `budget_alerts(budget, total_expense)` — returns alert dicts at 75%, 90%, 100% thresholds
- `budget_mood(budget, total_expense)` — returns mood ring state (`safe`, `watch`, `risk`, `over`)
- `can_manage_family_group(user, family_group)` — checks if user is the group creator
- `chart_payload(labels, values)` — JSON-safe chart data for template rendering
- `csv_response()` / `pdf_response()` — helper functions for file downloads

### Download Patterns
Several views support `?download=csv`, `?download=pdf`, `?download=transactions_csv`, and `?download=transactions_pdf` query parameters that return file responses instead of HTML.

---

## Forms

All forms are in `expenses/forms.py`. Every form uses `apply_bootstrap_widgets()` to add Bootstrap CSS classes to all fields.

| Form Class                    | Purpose                                            |
|-------------------------------|----------------------------------------------------|
| `RegisterForm`                | User registration (extends `UserCreationForm`), validates unique email + username, includes security question |
| `StyledAuthenticationForm`    | Login form that accepts User ID (numeric PK) **or** username |
| `PasswordResetEmailForm`      | Email input for password reset flow                |
| `SecurityAnswerForm`          | Security question answer during password reset     |
| `StyledSetPasswordForm`       | New password input (extends `SetPasswordForm`)     |
| `ExpenseForm`                 | Create expense (`ModelForm` for `Expense`)         |
| `ExpenseSearchForm`           | Multi-field search/filter for expense list          |
| `ReportFilterForm`            | Month/year selector for reports                    |
| `BudgetForm`                  | Personal budget setup (`ModelForm` for `Budget`)   |
| `FamilyBudgetForm`            | Family budget setup (`ModelForm` for `FamilyBudget`) |
| `FamilyTransactionFilterForm` | Filter family transactions by member, category, date range, etc. |
| `FamilyGroupForm`             | Create family group (`ModelForm` for `FamilyGroup`) |
| `JoinFamilyForm`              | Join family group by code                          |

---

## PDF Generation

`expenses/pdf_builder.py` implements a **raw PDF generator from scratch** — no external libraries (no ReportLab, no WeasyPrint). It builds PDF content using direct PDF stream operations.

- **Class**: `StatementPDF` — manages pages, fonts, content streams, object references
- **Entry point**: `build_statement_pdf(title, subtitle, details, summary_cards, charts, table_title, table_headers, table_rows, table_widths)` → returns `bytes`
- **Color constants**: `NAVY`, `TEAL`, `GREEN`, `CORAL`, `AMBER`, `MUTED`, `BORDER`, `SOFT_BG`, `WHITE`
- **Chart rendering**: Draws bar/line charts directly into PDF using raw drawing commands
- **Used for**: Personal monthly statements and family monthly/transaction statements

---

## Testing

All tests are in `expenses/tests.py` in a single `ExpenseManagementTests(TestCase)` class with 19 test methods.

### Test Coverage Areas
- **Registration**: Duplicate email rejection, security answer storage
- **Authentication**: Dashboard login required, numeric User ID login, username login
- **Password Reset**: Default security answer for existing accounts, signup answer, full 3-step flow
- **Data Isolation**: Users only see their own expenses
- **Budget**: Remaining budget on dashboard, budget carry-forward behavior
- **Family**: Family report includes members but not outsiders, family budget creator-only access, family budget form visibility, family budget carry-forward
- **Pages**: All authenticated pages render (200 status)
- **Filters**: Expense list custom date range filtering
- **Downloads**: Personal CSV/PDF download, family CSV/PDF download
- **Family Transactions**: Custom date range filter and download

### Running Tests
```bash
python manage.py test
```

---

## Key Domain Rules & Business Logic

### Budget Carry-Forward
Budgets are **not** copied monthly. Instead, the system finds the **most recent budget record** that is ≤ the current month/year using `effective_monthly_record()`. This means setting a budget in January carries forward to all subsequent months until a new budget is explicitly set.

### Budget Alerts
Three alert levels based on `(total_expense / budget.amount) * 100`:
- **≥75%**: Info — "You have used 75% of your monthly budget"
- **≥90%**: Warning — "You are close to your budget limit"
- **≥100%**: Danger — "Budget exceeded for this month"

### Budget Mood Ring
Dashboard displays a visual mood indicator:
- **≤50%**: `safe` / "Safe"
- **>50–75%**: `watch` / "Watch"
- **>75–90%**: `risk` / "Risk"
- **>90%**: `over` / "Over Budget"

### Family Budget Access Control
- Only the **group creator** (`FamilyGroup.created_by`) can set or update the family budget
- All members can **view** family reports and download statements
- Checked via `can_manage_family_group()` and enforced with `HttpResponseForbidden`

### Login by User ID
The `StyledAuthenticationForm` resolves numeric input as a User PK first (`User.objects.filter(pk=int(identifier))`), falling back to treating it as a username. This allows login via the numeric User ID displayed on registration.

### Password Reset Flow (3-step, session-based)
1. **Email lookup** → stores `password_reset_user_id` in session
2. **Security answer verification** → sets `password_reset_verified = True`
3. **New password form** → clears session keys on success
- Pre-existing accounts without a security answer get the default answer `"Kathmandu"`

### Family Group Codes
- 8-character uppercase alphanumeric codes, auto-generated on save
- Generated via `secrets.choice()` with collision checking
- Creator is automatically added as a member on group creation

---

## Coding Conventions

### Style
- **All views** are function-based with `@login_required` decorator (except `ExpenseLoginView` CBV)
- **Delete views** use `@require_POST` for safety
- **Form widgets** are styled via `apply_bootstrap_widgets()` — adds `form-control` or `form-select` classes
- **Messages framework** used throughout for user feedback (`messages.success`, `messages.error`, `messages.info`)
- **Template naming**: All templates live in `expenses/templates/expenses/` and follow `snake_case.html`

### Data Patterns
- Monetary values use `DecimalField(max_digits=12, decimal_places=2)` with `MinValueValidator(0.01)`
- All querysets filter by `user=request.user` to ensure data isolation
- Chart data is prepared via `chart_payload()` → JSON-serialized using `DjangoJSONEncoder`
- Summary helpers (`category_summary`, `daily_summary`) return dicts with both `total` (Decimal) and `value` (float) for template and chart compatibility

### Template Conventions
- `base.html` provides layout, Bootstrap 5 CDN, Bootstrap Icons CDN, Chart.js CDN
- Templates extend `base.html` and use `{% block content %}`
- Static files referenced via `{% static 'expenses/css/styles.css' %}` and `{% static 'expenses/js/charts.js' %}`
- CSRF tokens are included in all forms via `{% csrf_token %}`

---

## Settings & Configuration

Key settings in `expense_manager/settings.py`:

| Setting                 | Value                              |
|-------------------------|------------------------------------|
| `DEBUG`                 | `True` (development only)          |
| `SECRET_KEY`            | Insecure dev key (not for production) |
| `DATABASES`             | SQLite at `BASE_DIR / "db.sqlite3"` |
| `TIME_ZONE`             | `Asia/Kathmandu`                   |
| `USE_TZ`                | `True`                             |
| `LOGIN_URL`             | `"login"`                          |
| `LOGIN_REDIRECT_URL`    | `"dashboard"`                      |
| `LOGOUT_REDIRECT_URL`   | `"home"`                           |
| `STATIC_URL`            | `"static/"`                        |
| `DEFAULT_AUTO_FIELD`    | `BigAutoField`                     |
| `AUTH_PASSWORD_VALIDATORS` | All 4 default Django validators |

---

## Development Workflow

### Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Common Commands
```bash
python manage.py test                  # Run test suite
python manage.py makemigrations        # After model changes
python manage.py migrate               # Apply migrations
python manage.py runserver             # Dev server at http://127.0.0.1:8000/
```

### When Adding New Features
1. Add/modify models in `expenses/models.py`
2. Run `makemigrations` and `migrate`
3. Add forms in `expenses/forms.py` (use `apply_bootstrap_widgets()`)
4. Add views in `expenses/views.py` (use `@login_required`, filter by `user=request.user`)
5. Add URL pattern in `expenses/urls.py`
6. Create template in `expenses/templates/expenses/` (extend `base.html`)
7. Register in `expenses/admin.py` if needed
8. Add tests in `expenses/tests.py`

### When Modifying Existing Code
- Preserve all existing comments and docstrings unrelated to your changes
- Maintain the existing code style (function-based views, Django messages, Bootstrap widget styling)
- Always filter querysets by user for data isolation
- Use `Decimal` for monetary calculations, convert to `float` only for JSON/charts
- Keep the `apply_bootstrap_widgets()` pattern for any new forms
- Budget carry-forward logic (`effective_monthly_record()`) is critical — do not break it
