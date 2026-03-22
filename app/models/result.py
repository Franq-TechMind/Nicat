from datetime import datetime

from app import db


class AssessmentScheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    module_count = db.Column(db.Integer, default=1)
    raw_total = db.Column(db.Float, default=100)
    converted_total = db.Column(db.Float, default=100)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    components = db.relationship('AssessmentComponent', backref='scheme', lazy=True, cascade='all, delete-orphan')
    program_links = db.relationship('ProgramAssessmentScheme', backref='scheme', lazy=True, cascade='all, delete-orphan')


class AssessmentComponent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey('assessment_scheme.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    position = db.Column(db.Integer, default=1)


class ProgramAssessmentScheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False, unique=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey('assessment_scheme.id'), nullable=False)

    program = db.relationship('Program', backref='assessment_scheme_assignment', uselist=False)


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5), nullable=False)
    remarks = db.Column(db.String(50), default='Pending Review')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    entered_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    unit = db.relationship('Unit', backref='results')
    semester = db.relationship('Semester', backref='results')
    module_results = db.relationship('ModuleResult', backref='parent_result', lazy=True, cascade='all, delete-orphan')


class ModuleResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    module_number = db.Column(db.Integer, nullable=False)
    raw_total = db.Column(db.Float, default=0)
    converted_total = db.Column(db.Float, default=0)
    grade = db.Column(db.String(5))
    remarks = db.Column(db.String(50), default='Pending Review')

    component_scores = db.relationship('ModuleComponentScore', backref='module_result', lazy=True, cascade='all, delete-orphan')


class ModuleComponentScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_result_id = db.Column(db.Integer, db.ForeignKey('module_result.id'), nullable=False)
    component_name = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    score = db.Column(db.Float, nullable=False, default=0)
