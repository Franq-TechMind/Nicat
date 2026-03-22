from datetime import datetime

from app import db


class FeeInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.String(30), default='unpaid')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), default='cash')
    reference = db.Column(db.String(100))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
