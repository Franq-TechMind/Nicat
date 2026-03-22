from datetime import datetime

from app import db


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admission_number = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    address = db.Column(db.String(255))
    guardian_name = db.Column(db.String(120))
    guardian_phone = db.Column(db.String(20))
    status = db.Column(db.String(30), default='active')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    portal_ready = db.Column(db.Boolean, default=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)

    applications = db.relationship('Application', backref='student', lazy=True)
    payments = db.relationship('Payment', backref='student', lazy=True)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)
    results = db.relationship('Result', backref='student', lazy=True)
    invoices = db.relationship('FeeInvoice', backref='student', lazy=True)
    user_account = db.relationship('User', backref='student_account', uselist=False)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def total_invoiced(self):
        return sum(invoice.amount for invoice in self.invoices)

    @property
    def total_paid(self):
        return sum(payment.amount for payment in self.payments)

    @property
    def total_balance(self):
        return max(self.total_invoiced - self.total_paid, 0)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_number = db.Column(db.String(50), unique=True, nullable=False)
    applicant_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(30), default='pending')
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    unit = db.relationship('Unit', backref='enrollments')
    semester = db.relationship('Semester', backref='enrollments')
