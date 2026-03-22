from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import StudentForm
from app.models import AttendanceRecord, FeeInvoice, Payment, Program, Result, Student
from app.utils import permission_required

students_bp = Blueprint('students', __name__)


def lecturer_program_ids():
    return sorted({item.unit.program_id for item in current_user.lecturer_units}) if current_user.role == 'lecturer' and current_user.lecturer_units else []


def populate_programs(form):
    if current_user.role == 'lecturer' and current_user.lecturer_units:
        programs = Program.query.filter(Program.id.in_(lecturer_program_ids())).order_by(Program.name).all()
    else:
        programs = Program.query.order_by(Program.name).all()
    form.program_id.choices = [(p.id, f'{p.name} ({p.code})') for p in programs]


@students_bp.route('/students')
@login_required
@permission_required('students.view')
def index():
    q = request.args.get('q', '').strip()
    query = Student.query
    if current_user.role == 'lecturer' and current_user.lecturer_units:
        query = query.filter(Student.program_id.in_(lecturer_program_ids()))
    if q:
        query = query.filter(Student.first_name.ilike(f'%{q}%') | Student.last_name.ilike(f'%{q}%') | Student.admission_number.ilike(f'%{q}%'))
    students = query.order_by(Student.id.desc()).all()
    return render_template('students/index.html', students=students, q=q)


@students_bp.route('/students/new', methods=['GET', 'POST'])
@login_required
@permission_required('students.create')
def create():
    form = StudentForm(); populate_programs(form)
    if form.validate_on_submit():
        student = Student(); form.populate_obj(student)
        if student.email:
            student.email = student.email.lower()
        db.session.add(student); db.session.commit(); flash('Student created successfully.', 'success'); return redirect(url_for('students.index'))
    return render_template('students/form.html', form=form, title='New Student')


@students_bp.route('/students/lecturer-workspace')
@login_required
@permission_required('students.view')
def lecturer_workspace():
    if current_user.role != 'lecturer':
        return redirect(url_for('students.index'))
    students = Student.query.filter(Student.program_id.in_(lecturer_program_ids())).order_by(Student.first_name).all() if lecturer_program_ids() else []
    at_risk = []
    for student in students:
        total = len(student.attendance_records)
        approved_present = len([x for x in student.attendance_records if x.approval_status == 'approved' and x.status == 'present'])
        percent = (approved_present / total * 100) if total else 0
        if total and percent < 75:
            at_risk.append((student, round(percent, 2)))
    return render_template('students/lecturer_workspace.html', students=students, at_risk=at_risk)


@students_bp.route('/students/<int:student_id>')
@login_required
@permission_required('students.view')
def detail(student_id):
    student = Student.query.get_or_404(student_id)
    invoices = FeeInvoice.query.filter_by(student_id=student.id).order_by(FeeInvoice.created_at.desc()).all()
    payments = Payment.query.filter_by(student_id=student.id).order_by(Payment.paid_at.desc()).all()
    results = Result.query.filter_by(student_id=student.id).order_by(Result.created_at.desc()).all()
    attendance = AttendanceRecord.query.filter_by(student_id=student.id).order_by(AttendanceRecord.attendance_date.desc()).all()
    attendance_total = len(attendance)
    attendance_present = len([x for x in attendance if x.approval_status == 'approved' and x.status == 'present'])
    attendance_percent = round((attendance_present / attendance_total * 100), 2) if attendance_total else 0
    return render_template('students/detail.html', student=student, invoices=invoices, payments=payments, results=results, attendance=attendance, attendance_percent=attendance_percent)


@students_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('students.edit')
def edit(student_id):
    student = Student.query.get_or_404(student_id)
    form = StudentForm(obj=student); populate_programs(form)
    if form.validate_on_submit():
        form.populate_obj(student)
        if student.email:
            student.email = student.email.lower()
        db.session.commit(); flash('Student updated successfully.', 'success'); return redirect(url_for('students.index'))
    return render_template('students/form.html', form=form, title='Edit Student')


@students_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@login_required
@permission_required('students.delete')
def delete(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student); db.session.commit(); flash('Student deleted.', 'info'); return redirect(url_for('students.index'))


@students_bp.route('/student-portal')
@login_required
def portal():
    if current_user.role != 'student' or not current_user.student_id:
        return redirect(url_for('main.dashboard'))
    student = Student.query.get_or_404(current_user.student_id)
    invoices = FeeInvoice.query.filter_by(student_id=student.id).order_by(FeeInvoice.created_at.desc()).all()
    payments = Payment.query.filter_by(student_id=student.id).order_by(Payment.paid_at.desc()).all()
    results = Result.query.filter_by(student_id=student.id).order_by(Result.created_at.desc()).all()
    attendance = AttendanceRecord.query.filter_by(student_id=student.id).order_by(AttendanceRecord.attendance_date.desc()).all()
    attendance_total = len(attendance)
    attendance_present = len([x for x in attendance if x.approval_status == 'approved' and x.status == 'present'])
    attendance_percent = round((attendance_present / attendance_total * 100), 2) if attendance_total else 0
    return render_template('students/portal.html', student=student, invoices=invoices, payments=payments, results=results, attendance=attendance, attendance_percent=attendance_percent)
