from app import db


class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    lecturer_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    room = db.Column(db.String(50))

    unit = db.relationship('Unit', backref='timetable_entries')
    lecturer = db.relationship('User', backref='timetable_entries')
