from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import DevelopmentConfig

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


def seed_data():
    from app.models import AcademicYear, AssessmentComponent, AssessmentScheme, Department, Program, ProgramAssessmentScheme, Semester, Unit

    department_specs = [('ICT', 'ICT / Computing', 'Technology and computing programs'), ('BUS', 'Business / Finance', 'Business and accounting programs')]
    departments = {}
    for code, name, description in department_specs:
        dept = Department.query.filter_by(code=code).first()
        if not dept:
            dept = Department(name=name, code=code, description=description)
            db.session.add(dept)
            db.session.flush()
        departments[code] = dept

    program_specs = [
        ('CAB', 'Computer Application for Business', 'Certificate', 1, 'ICT'),
        ('GDS', 'Graphics Design', 'Certificate', 1, 'ICT'),
        ('PRG', 'Programming', 'Certificate', 1, 'ICT'),
        ('ACC', 'Accounting', 'Certificate', 1, 'BUS'),
    ]
    for code, name, level, duration, dept_code in program_specs:
        program = Program.query.filter_by(code=code).first()
        if not program:
            program = Program(name=name, code=code, level=level, duration_years=duration, department_id=departments[dept_code].id)
            db.session.add(program)
        else:
            program.name = name
            program.level = level
            program.duration_years = duration
            program.department_id = departments[dept_code].id
    db.session.flush()

    year = AcademicYear.query.filter_by(name='2026/2027').first()
    if not year:
        year = AcademicYear(name='2026/2027', is_current=True)
        db.session.add(year)
        db.session.flush()

    for sem_name, is_current in [('Semester 1', True), ('Semester 2', False)]:
        sem = Semester.query.filter_by(name=sem_name, academic_year_id=year.id).first()
        if not sem:
            db.session.add(Semester(name=sem_name, academic_year_id=year.id, is_current=is_current))

    db.session.flush()

    programs = {p.code: p for p in Program.query.all()}
    unit_specs = [
        ('CAB101', 'Computer Fundamentals', 3, 'CAB'), ('CAB102', 'Microsoft Word and Excel', 3, 'CAB'), ('CAB103', 'Business Communication', 2, 'CAB'),
        ('GDS101', 'Design Principles', 3, 'GDS'), ('GDS102', 'Adobe Photoshop', 3, 'GDS'), ('GDS103', 'CorelDraw and Branding', 3, 'GDS'),
        ('PRG101', 'Introduction to Programming', 3, 'PRG'), ('PRG102', 'Python Programming', 3, 'PRG'), ('PRG103', 'Web Development Basics', 3, 'PRG'),
        ('ACC101', 'Accounting Fundamentals', 3, 'ACC'), ('ACC102', 'Bookkeeping', 3, 'ACC'), ('ACC103', 'Financial Statements', 3, 'ACC'),
    ]
    for code, name, credit_hours, program_code in unit_specs:
        unit = Unit.query.filter_by(code=code).first()
        if not unit:
            db.session.add(Unit(name=name, code=code, credit_hours=credit_hours, program_id=programs[program_code].id))

    db.session.flush()

    cab_scheme = AssessmentScheme.query.filter_by(name='CAB 3-Module Scheme').first()
    if not cab_scheme:
        cab_scheme = AssessmentScheme(name='CAB 3-Module Scheme', module_count=3, raw_total=110, converted_total=100, is_active=True)
        db.session.add(cab_scheme)
        db.session.flush()

    for name, max_marks, position in [('CAT', 30, 1), ('Group Work', 20, 2), ('Final Exam', 60, 3)]:
        component = AssessmentComponent.query.filter_by(scheme_id=cab_scheme.id, name=name).first()
        if not component:
            db.session.add(AssessmentComponent(scheme_id=cab_scheme.id, name=name, max_marks=max_marks, position=position))

    cab_assignment = ProgramAssessmentScheme.query.filter_by(program_id=programs['CAB'].id).first()
    if not cab_assignment:
        db.session.add(ProgramAssessmentScheme(program_id=programs['CAB'].id, scheme_id=cab_scheme.id))
    else:
        cab_assignment.scheme_id = cab_scheme.id

    db.session.commit()


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.main import main_bp
    from app.auth import auth_bp
    from app.academics import academics_bp
    from app.students import students_bp
    from app.admissions import admissions_bp
    from app.finance import finance_bp
    from app.results import results_bp
    from app.attendance import attendance_bp
    from app.lecturers import lecturers_bp
    from app.models import User, LecturerUnitAssignment, LecturerStudentAssignment, Department, Program, AcademicYear, Semester, Unit, Student, Application, Enrollment, FeeInvoice, Payment, Result, AssessmentScheme, AssessmentComponent, ProgramAssessmentScheme, ModuleResult, ModuleComponentScore, AttendanceRecord, TimetableEntry

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(academics_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(admissions_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(lecturers_bp)

    with app.app_context():
        db.create_all()
        seed_data()

    return app
