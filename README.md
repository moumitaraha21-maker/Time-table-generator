# Smart Timetable Generator 📅

An AI-powered web application for automatically generating optimal school/college timetables using genetic algorithms.

## Features ✨

- **AI-Powered Generation**: Uses genetic algorithms to create conflict-free, optimized timetables
- **Role-Based Access**: Separate dashboards for Admin, Teachers, and Students
- **Constraint Management**: Handles both hard constraints (teacher conflicts, room availability) and soft constraints (teacher preferences, gap minimization)
- **Modern UI**: Beautiful, responsive design with gradient backgrounds and smooth animations
- **Export Options**: Export timetables to PDF and Excel formats
- **Real-time Visualization**: Color-coded timetable grid with clear subject visualization

## Technology Stack 🛠️

**Backend:**
- Python 3.8+
- Flask (Web Framework)
- SQLAlchemy (ORM)
- DEAP (Genetic Algorithm Library)
- Flask-Login (Authentication)

**Frontend:**
- HTML5
- CSS3 (Modern gradients, animations, flexbox/grid)
- Vanilla JavaScript
- SVG Icons

**Database:**
- SQLite (Development)
- PostgreSQL (Production - recommended)

## Installation 🚀

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd "time table"
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

## First Time Setup 📋

1. **Login with Default Admin Account:**
   - Email: `admin@school.edu`
   - Password: `admin123`

2. **Add Master Data:**
   - Navigate to "Subjects" and add your school subjects
   - Navigate to "Teachers" and add teaching staff
   - Navigate to "Classrooms" and add available rooms
   - Navigate to "Classes" and add class sections

3. **Generate Timetable:**
   - Go to "Generate" in the navigation
   - Enter timetable name
   - Configure algorithm parameters (optional)
   - Click "Generate Timetable"
   - Wait for the genetic algorithm to complete (1-3 minutes)

4. **View & Export:**
   - View the generated timetable
   - Export to PDF or Excel
   - Share with teachers and students

## Usage Guide 👥

### Admin Dashboard
- Manage all master data (subjects, teachers, classrooms, classes)
- Generate new timetables
- View and export timetables
- Monitor system statistics

### Teacher Dashboard
- View personal teaching schedule
- See assigned classes and rooms
- Track weekly teaching hours

### Student Dashboard
- View class timetable
- Access homework and assignments
- Get notifications for schedule changes

## Genetic Algorithm Details 🧬

The timetable generation uses a genetic algorithm with:

**Fitness Evaluation:**
- Hard Constraints: Teacher conflicts (-1000), Room conflicts (-1000)
- Soft Constraints: Gap minimization (+5), Even distribution (+8)

**Parameters:**
- Population Size: 50
- Max Generations: 200
- Crossover Rate: 0.8
- Mutation Rate: 0.15
- Tournament Size: 5

**Process:**
1. Initialize random population of timetables
2. Evaluate fitness of each solution
3. Select best parents using tournament selection
4. Create offspring through crossover
5. Apply mutations for diversity
6. Repeat until optimal solution found

## Project Structure 📁

```
time table/
├── app.py                          # Main Flask application
├── genetic_algorithm.py            # GA implementation
├── export_utils.py                 # PDF/Excel export
├── requirements.txt                # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css              # Modern CSS styling
│   └── js/
│       └── main.js                # JavaScript utilities
├── templates/
│   ├── base.html                  # Base template
│   ├── login.html                 # Login page
│   ├── register.html              # Registration page
│   ├── timetable_view.html        # Timetable visualization
│   ├── admin/
│   │   ├── dashboard.html         # Admin dashboard
│   │   ├── subjects.html          # Subject management
│   │   ├── teachers.html          # Teacher management
│   │   ├── classrooms.html        # Classroom management
│   │   ├── classes.html           # Class management
│   │   └── generate_timetable.html # Timetable generation
│   ├── teacher/
│   │   └── dashboard.html         # Teacher dashboard
│   └── student/
│       └── dashboard.html         # Student dashboard
└── exports/                        # Generated PDF/Excel files
```

## Configuration ⚙️

### Database Configuration
Edit `app.py` to change database:

```python
# SQLite (Development)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable.db'

# PostgreSQL (Production)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/timetable'
```

### Secret Key
Change the secret key in production:

```python
app.config['SECRET_KEY'] = 'your-secure-secret-key-here'
```

## API Endpoints 🔌

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Admin
- `GET /admin/dashboard` - Admin dashboard
- `GET/POST /admin/subjects` - Manage subjects
- `GET/POST /admin/teachers` - Manage teachers
- `GET/POST /admin/classrooms` - Manage classrooms
- `GET/POST /admin/classes` - Manage classes
- `GET/POST /admin/generate-timetable` - Generate timetable

### Timetable
- `GET /timetable/<id>` - View timetable
- `GET /api/timetable/<id>/export/pdf` - Export as PDF
- `GET /api/timetable/<id>/export/excel` - Export as Excel

## Troubleshooting 🔧

### Common Issues

**Database not created:**
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

**Import errors:**
```bash
pip install -r requirements.txt --upgrade
```

**Port already in use:**
```python
# Change port in app.py
app.run(port=5001)
```

## Future Enhancements 🚀

- [ ] Multi-campus support
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Real-time notifications
- [ ] Machine learning optimization
- [ ] Mobile app (React Native)
- [ ] REST API for third-party integrations
- [ ] Advanced analytics and reporting

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This project is licensed under the MIT License.

## Support 💬

For issues and questions:
- Create an issue on GitHub
- Email: support@smarttimetable.com

## Credits 👏

Developed with ❤️ using:
- Flask
- DEAP (Genetic Algorithm Library)
- ReportLab (PDF Generation)
- OpenPyXL (Excel Generation)

---

**Made with ❤️ for Educational Institutions**
