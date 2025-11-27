#!/bin/bash
# Phronesis LEX Backend Startup Script

cd "$(dirname "$0")/backend"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Initialize database if needed
echo "Initializing database..."
python -c "from db.connection import init_db_sync; init_db_sync()"

# Start server
echo "Starting Phronesis LEX Backend..."
echo "API available at http://127.0.0.1:8000"
echo "API docs at http://127.0.0.1:8000/docs"
python app.py
