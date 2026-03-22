from datetime import datetime

from app import db


class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='present')
    source = db.Column(db.String(20), nullable=False, default='lecturer')
    approval_status = db.Column(db.String(20), nullable=False, default='approved')
    submitted_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='attendance_records')
    unit = db.relationship('Unit', backref='attendance_records')
    submitted_by = db.relationship('User', foreign_keys=[submitted_by_user_id], backref='submitted_attendance')
    approved_by = db.relationship('User', foreign_keys=[approved_by_user_id], backref='approved_attendance')
