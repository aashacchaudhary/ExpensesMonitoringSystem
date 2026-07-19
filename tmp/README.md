# Expense Management System

A complete Django-based Expense Management website for tracking personal expenses, monthly budgets, budget alerts, reports, and family-level expense summaries with Chart.js graphs.

## Tech Stack

- Backend: Python, Django
- Database: SQLite
- Authentication: Django built-in authentication system
- Frontend: Django Templates, HTML5, CSS3, JavaScript
- UI Framework: Bootstrap 5
- Icons: Bootstrap Icons
- Charts: Chart.js
- Styling Theme: Expense Monitoring System, using custom responsive CSS and soft dashboard cards

## Features

- User registration with duplicate username and email validation
- Secure login by User ID or username, logout, and protected dashboard pages using Django authentication
- Forgot-password flow using Gmail/email lookup, the fixed security question "What is your dream place ?", and a new password form
- Add, view, search, filter, and delete personal expenses
- Dashboard totals for current month, today's expenses, remaining budget, record count, recent expenses, and charts
- Monthly reports with total expense, category summary, daily summary, highest category, expense list, and bank-style PDF statements with budget usage and charts
- Monthly budget setup with 75%, 90%, and exceeded budget alerts
- Family groups with generated join codes
- Join family groups by code and view family members
- Family monthly statements with combined totals, member-wise summaries, category summaries, daily summaries, graphs, and bank-style PDF downloads
- Creator-managed family budgets that stay separate from each user's personal budget
- Family transaction filtering by custom date range with downloadable CSV and PDF statements
- Responsive Bootstrap UI for desktop, tablet, and mobile
- Django admin support for all app models
- Basic automated tests for registration, authorization, budgets, and family report privacy

## Installation

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Database Setup

Create model migrations:

```bash
python manage.py makemigrations
```

Apply migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

## Run the Development Server

```bash
python manage.py runserver
```

Open the site at:

```text
http://127.0.0.1:8000/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

## Default Test Usage

Run the included test suite:

```bash
python manage.py test
```

The tests cover duplicate email validation, login protection, user data isolation, dashboard budget calculations, and family report privacy.
