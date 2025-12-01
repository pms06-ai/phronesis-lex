@echo off
echo Starting Phronesis LEX Backend...
cd %~dp0..\django_backend

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Running setup...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seed_legal_rules
)

echo.
echo Django server starting on http://localhost:8000
echo API available at http://localhost:8000/api/
echo Admin available at http://localhost:8000/admin/
echo.

python manage.py runserver

