@echo off
echo ===================================
echo Smart Timetable Generator Setup
echo ===================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error creating virtual environment
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate

echo [3/4] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies
    pause
    exit /b 1
)

echo [4/4] Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"

echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo To start the application:
echo 1. Run: venv\Scripts\activate
echo 2. Run: python app.py
echo 3. Open: http://localhost:5000
echo.
echo Default Admin Login:
echo Email: admin@school.edu
echo Password: admin123
echo.
pause
