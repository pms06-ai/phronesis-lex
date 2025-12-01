@echo off
echo ===============================================
echo Phronesis LEX - Setup Script
echo Forensic Case Intelligence Platform v5.0
echo ===============================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Check for Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    exit /b 1
)

echo [1/5] Creating virtual environment...
cd django_backend
if not exist venv (
    python -m venv venv
)

echo [2/5] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo [3/5] Running database migrations...
python manage.py migrate

echo [4/5] Seeding legal rules...
python manage.py seed_legal_rules

echo [5/5] Installing frontend dependencies...
cd ..\frontend
call npm install

echo.
echo ===============================================
echo Setup complete!
echo.
echo To start the backend:
echo   cd django_backend
echo   venv\Scripts\activate
echo   python manage.py runserver
echo.
echo To start the frontend:
echo   cd frontend
echo   npm run dev
echo ===============================================

