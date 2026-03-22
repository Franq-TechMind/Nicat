from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')
    password_hash = db.Column(db.String(255), nullable=False)
    is_active_user = db.Column(db.Boolean, default=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    staff_id = db.Column(db.String(50), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    department_name = db.Column(db.String(120), nullable=True)
    specialization = db.Column(db.String(120), nullable=True)

    lecturer_units = db.relationship('LecturerUnitAssignment', backref='lecturer', lazy=True, cascade='all, delete-orphan')
    lecturer_students = db.relationship('LecturerStudentAssignment', backref='lecturer', lazy=True, cascade='all, delete-orphan')
    entered_results = db.relationship('Result', backref='entered_by_user', lazy=True, foreign_keys='Result.entered_by')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_user

    def __repr__(self):
        return f'<User {self.email}>'


class LecturerUnitAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lecturer_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)

    unit = db.relationship('Unit', backref='lecturer_assignments')


class LecturerStudentAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lecturer_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

    student = db.relationship('Student', backref='lecturer_assignments')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
