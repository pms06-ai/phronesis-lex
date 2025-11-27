@echo off
REM Phronesis LEX Backend Startup Script (Windows)

cd /d "%~dp0backend"

REM Check for virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Checking dependencies...
pip install -q -r requirements.txt

REM Initialize database
echo Initializing database...
python -c "from db.connection import init_db_sync; init_db_sync()"

REM Start server
echo Starting Phronesis LEX Backend...
echo API available at http://127.0.0.1:8000
echo API docs at http://127.0.0.1:8000/docs
python app.py
