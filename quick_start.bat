@echo off
echo Installing dependencies and starting Smart Timetable Generator...
echo.
pip install Flask Flask-SQLAlchemy Flask-Login Flask-CORS Werkzeug python-dotenv numpy pandas DEAP reportlab openpyxl Jinja2
echo.
echo Starting application...
python app.py
echo.
echo Opening in browser...
timeout /t 3 /nobreak
start chrome http://localhost:5000
