from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
from genetic_algorithm import GeneticAlgorithm
from export_utils import export_to_pdf, export_to_excel

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============================================
# DATABASE MODELS
# ============================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    duration = db.Column(db.Integer, default=45)
    color = db.Column(db.String(7), default='#3498db')
    requires_lab = db.Column(db.Boolean, default=False)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    employee_id = db.Column(db.String(50), unique=True)
    department = db.Column(db.String(100))
    max_hours_per_day = db.Column(db.Integer, default=6)
    max_hours_per_week = db.Column(db.Integer, default=30)
    qualified_subjects = db.Column(db.Text)  # JSON array
    preferences = db.Column(db.Text)  # JSON

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    building = db.Column(db.String(100))
    capacity = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(50))  # regular, lab, auditorium
    equipment = db.Column(db.Text)  # JSON

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10))
    student_count = db.Column(db.Integer)

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='draft')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    fitness_score = db.Column(db.Float)
    constraints = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('classroom.id'))
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday
    period_number = db.Column(db.Integer)
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))

# ============================================
# LOGIN MANAGER
# ============================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================
# ROUTES - Authentication
# ============================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already exists')
        
        user = User(email=email, role=role, first_name=first_name, last_name=last_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ============================================
# ROUTES - Admin Dashboard
# ============================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    stats = {
        'total_subjects': Subject.query.count(),
        'total_teachers': Teacher.query.count(),
        'total_classrooms': Classroom.query.count(),
        'total_classes': Class.query.count(),
        'total_timetables': Timetable.query.count()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        subject = Subject(
            name=request.form.get('name'),
            code=request.form.get('code'),
            duration=int(request.form.get('duration', 45)),
            color=request.form.get('color', '#3498db'),
            requires_lab=request.form.get('requires_lab') == 'on'
        )
        db.session.add(subject)
        db.session.commit()
        return redirect(url_for('manage_subjects'))
    
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@app.route('/admin/teachers', methods=['GET', 'POST'])
@login_required
def manage_teachers():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        teacher = Teacher(
            employee_id=request.form.get('employee_id'),
            department=request.form.get('department'),
            max_hours_per_day=int(request.form.get('max_hours_per_day', 6)),
            max_hours_per_week=int(request.form.get('max_hours_per_week', 30)),
            qualified_subjects=request.form.get('qualified_subjects', '[]')
        )
        db.session.add(teacher)
        db.session.commit()
        return redirect(url_for('manage_teachers'))
    
    teachers = Teacher.query.all()
    subjects = Subject.query.all()
    return render_template('admin/teachers.html', teachers=teachers, subjects=subjects)

@app.route('/admin/classrooms', methods=['GET', 'POST'])
@login_required
def manage_classrooms():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        classroom = Classroom(
            name=request.form.get('name'),
            building=request.form.get('building'),
            capacity=int(request.form.get('capacity')),
            room_type=request.form.get('room_type', 'regular')
        )
        db.session.add(classroom)
        db.session.commit()
        return redirect(url_for('manage_classrooms'))
    
    classrooms = Classroom.query.all()
    return render_template('admin/classrooms.html', classrooms=classrooms)

@app.route('/admin/classes', methods=['GET', 'POST'])
@login_required
def manage_classes():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        class_obj = Class(
            grade=request.form.get('grade'),
            section=request.form.get('section'),
            student_count=int(request.form.get('student_count', 0))
        )
        db.session.add(class_obj)
        db.session.commit()
        return redirect(url_for('manage_classes'))
    
    classes = Class.query.all()
    return render_template('admin/classes.html', classes=classes)

@app.route('/admin/generate-timetable', methods=['GET', 'POST'])
@login_required
def generate_timetable():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        timetable = Timetable(
            name=request.form.get('name'),
            created_by=current_user.id,
            status='generating'
        )
        db.session.add(timetable)
        db.session.commit()
        
        # Run genetic algorithm
        ga = GeneticAlgorithm(timetable.id)
        result = ga.run()
        
        timetable.status = 'generated'
        timetable.fitness_score = result['fitness']
        db.session.commit()
        
        return redirect(url_for('view_timetable', timetable_id=timetable.id))
    
    return render_template('admin/generate_timetable.html')

@app.route('/timetable/<int:timetable_id>')
@login_required
def view_timetable(timetable_id):
    timetable = Timetable.query.get_or_404(timetable_id)
    entries = TimetableEntry.query.filter_by(timetable_id=timetable_id).all()
    
    # Organize entries by class and day
    schedule_data = {}
    for entry in entries:
        class_key = f"Class {entry.class_id}"
        if class_key not in schedule_data:
            schedule_data[class_key] = {}
        
        day = entry.day_of_week
        if day not in schedule_data[class_key]:
            schedule_data[class_key][day] = {}
        
        schedule_data[class_key][day][entry.period_number] = {
            'subject': Subject.query.get(entry.subject_id),
            'teacher': Teacher.query.get(entry.teacher_id),
            'room': Classroom.query.get(entry.room_id),
            'time': f"{entry.start_time} - {entry.end_time}"
        }
    
    return render_template('timetable_view.html', 
                         timetable=timetable, 
                         schedule_data=schedule_data)

# ============================================
# ROUTES - Teacher Dashboard
# ============================================

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        return redirect(url_for('index'))
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        return "Teacher profile not found", 404
    
    # Get latest published timetable
    latest_timetable = Timetable.query.filter_by(status='published').order_by(Timetable.created_at.desc()).first()
    
    if latest_timetable:
        entries = TimetableEntry.query.filter_by(
            timetable_id=latest_timetable.id,
            teacher_id=teacher.id
        ).all()
    else:
        entries = []
    
    return render_template('teacher/dashboard.html', teacher=teacher, entries=entries)

# ============================================
# ROUTES - Student Dashboard
# ============================================

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    
    # Get student's class and timetable
    latest_timetable = Timetable.query.filter_by(status='published').order_by(Timetable.created_at.desc()).first()
    
    return render_template('student/dashboard.html', timetable=latest_timetable)

# ============================================
# API ROUTES
# ============================================

@app.route('/api/subjects')
@login_required
def api_subjects():
    subjects = Subject.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'code': s.code,
        'duration': s.duration,
        'color': s.color
    } for s in subjects])

@app.route('/api/timetable/<int:timetable_id>/export/pdf')
@login_required
def export_pdf(timetable_id):
    pdf_path = export_to_pdf(timetable_id)
    return send_file(pdf_path, as_attachment=True)

@app.route('/api/timetable/<int:timetable_id>/export/excel')
@login_required
def export_excel(timetable_id):
    excel_path = export_to_excel(timetable_id)
    return send_file(excel_path, as_attachment=True)

# ============================================
# INITIALIZE DATABASE
# ============================================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(email='admin@school.edu').first():
            admin = User(
                email='admin@school.edu',
                role='admin',
                first_name='Admin',
                last_name='User'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@school.edu / admin123")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
