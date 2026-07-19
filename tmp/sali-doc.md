Great question! Since you're on **Windows** and your project uses **Django** with **SQLite**, here’s exactly how to get it running.

### Important Note about the Batch Files
The files `generate-structure.bat` and `copy_to_tmp.bat` are **helper scripts** (they aren't required to run the Django app). The app runs purely through `manage.py`. So don't worry about those.

---

## Step-by-Step Launch Guide (Windows CMD)

**Make sure you are in the project folder:**
```
C:\Users\StudyAcer\Documents\GitHub\ExpensesMonitoringSystem>
```

### 1. Create and activate a virtual environment
*(If you already have a `venv` or `.venv` folder, skip creation and just activate it.)*

```cmd
python -m venv venv
venv\Scripts\activate
```
*(You should see `(venv)` appear at the beginning of your command line.)*

> **Troubleshooting:** If you get an error like *"Activate.ps1 cannot be loaded"*, just close PowerShell and open a **Command Prompt (CMD)** instead, or run:
> ```
> venv\Scripts\activate.bat
> ```

### 2. Install dependencies
```cmd
pip install -r requirements.txt
```
*(This installs Django 5.x.)*

### 3. Run database migrations
*(This creates the `db.sqlite3` file and sets up all tables.)*
```cmd
python manage.py migrate
```

### 4. (Optional) Create an admin user
This lets you log into the Django admin panel later.
```cmd
python manage.py createsuperuser
```
*(Follow the prompts for username, email, and password.)*

### 5. Start the development server
```cmd
python manage.py runserver
```

### 6. Open your browser
Visit: **http://127.0.0.1:8000/**

You should see the **Expense Monitoring System** home page.

---

## How to log in / register

- **Register** a new account using the "Create Account" button.
- Or use the **superuser** account you just created.
- **Login** accepts either your **Username** or your numeric **User ID** (shown after registration).

---

## Common "Gotchas" & Fixes

| Issue | Solution |
| :--- | :--- |
| **`python` is not recognized** | Python isn't installed, or it's not in your PATH. Install Python from python.org and check "Add to PATH". |
| **Port 8000 is busy** | Run the server on a different port: <br> `python manage.py runserver 8001` <br> Then visit `http://127.0.0.1:8001/` |
| **Migrations error (table already exists)** | If you have an old `db.sqlite3` file, delete it and run `migrate` fresh. |
| **Charts don't load** | Make sure you have internet access (Chart.js and Bootstrap are loaded from CDN). Or clear your browser cache. |
| **Static files (CSS) missing** | The CSS is served from the `static/` folder during development. If missing, run: <br> `python manage.py collectstatic` (though it's not strictly required with `DEBUG=True`). |

---

## Want to test it immediately?

The project already includes **automated tests**. Once the server is running, open a *new* terminal, activate the environment, and run:

```cmd
python manage.py test
```

This verifies that everything (authentication, budgets, family reports, PDF downloads) is working correctly. 🚀