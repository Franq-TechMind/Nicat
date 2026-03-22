from datetime import datetime

from app import db


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    programs = db.relationship('Program', backref='department', lazy=True)


class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    level = db.Column(db.String(50), nullable=False)
    duration_years = db.Column(db.Integer, default=1)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    units = db.relationship('Unit', backref='program', lazy=True)
    students = db.relationship('Student', backref='program', lazy=True)


class AcademicYear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    is_current = db.Column(db.Boolean, default=False)

    semesters = db.relationship('Semester', backref='academic_year', lazy=True)


class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_year.id'), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False)


class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    credit_hours = db.Column(db.Integer, default=1)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
