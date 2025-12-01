@echo off
echo Starting Phronesis LEX Frontend...
cd %~dp0..\frontend

if not exist node_modules (
    echo Installing dependencies...
    call npm install
)

echo.
echo Frontend starting on http://localhost:5173
echo.

call npm run dev

