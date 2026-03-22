from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import AttendanceApprovalForm, AttendanceForm, BulkAttendanceForm
from app.models import AttendanceRecord, Student, Unit
from app.utils import lecturer_owns_unit, permission_required

attendance_bp = Blueprint('attendance', __name__)


def available_units_for_user():
    if current_user.role == 'lecturer':
        assigned_ids = [item.unit_id for item in current_user.lecturer_units]
        return Unit.query.filter(Unit.id.in_(assigned_ids)).order_by(Unit.name).all() if assigned_ids else []
    if current_user.role == 'student' and current_user.student_id:
        student = Student.query.get(current_user.student_id)
        return Unit.query.filter_by(program_id=student.program_id).order_by(Unit.name).all() if student else []
    return Unit.query.order_by(Unit.name).all()


def available_students_for_user():
    if current_user.role == 'lecturer':
        program_ids = list({item.unit.program_id for item in current_user.lecturer_units})
        return Student.query.filter(Student.program_id.in_(program_ids)).order_by(Student.first_name).all() if program_ids else []
    if current_user.role == 'student' and current_user.student_id:
        student = Student.query.get(current_user.student_id)
        return [student] if student else []
    return Student.query.order_by(Student.first_name).all()


def populate_choices(form):
    form.student_id.choices = [(s.id, f'{s.full_name} - {s.admission_number}') for s in available_students_for_user()]
    form.unit_id.choices = [(u.id, f'{u.name} ({u.code})') for u in available_units_for_user()]


@attendance_bp.route('/attendance')
@login_required
@permission_required('attendance.view')
def index():
    records = AttendanceRecord.query.order_by(AttendanceRecord.attendance_date.desc(), AttendanceRecord.id.desc()).all()
    if current_user.role == 'lecturer':
        unit_ids = [item.unit_id for item in current_user.lecturer_units]
        records = [r for r in records if r.unit_id in unit_ids]
    elif current_user.role == 'student' and current_user.student_id:
        records = [r for r in records if r.student_id == current_user.student_id]
    pending_count = len([r for r in records if r.approval_status == 'pending'])
    return render_template('attendance/index.html', records=records, pending_count=pending_count)


@attendance_bp.route('/attendance/new', methods=['GET', 'POST'])
@login_required
@permission_required('attendance.create')
def create():
    form = AttendanceForm()
    populate_choices(form)
    if current_user.role == 'student' and current_user.student_id:
        form.student_id.data = current_user.student_id
    if form.validate_on_submit():
        if current_user.role == 'lecturer' and not lecturer_owns_unit(current_user, form.unit_id.data):
            flash('You can only mark attendance for your assigned units.', 'danger')
            return render_template('attendance/form.html', form=form, title='New Attendance Record')
        if current_user.role == 'student' and form.student_id.data != current_user.student_id:
            flash('Students can only submit attendance for themselves.', 'danger')
            return render_template('attendance/form.html', form=form, title='Submit Attendance')
        existing = AttendanceRecord.query.filter_by(student_id=form.student_id.data, unit_id=form.unit_id.data, attendance_date=form.attendance_date.data).first()
        if existing:
            flash('Attendance for this student, unit and date already exists.', 'warning')
            return render_template('attendance/form.html', form=form, title='New Attendance Record' if current_user.role != 'student' else 'Submit Attendance')
        approval_status = 'approved' if current_user.role == 'lecturer' else 'pending'
        record = AttendanceRecord(student_id=form.student_id.data, unit_id=form.unit_id.data, attendance_date=form.attendance_date.data, status=form.status.data, source='lecturer' if current_user.role == 'lecturer' else 'student', approval_status=approval_status, submitted_by_user_id=current_user.id, approved_by_user_id=current_user.id if current_user.role == 'lecturer' else None, notes=form.notes.data)
        db.session.add(record)
        db.session.commit()
        flash('Attendance saved successfully.', 'success')
        return redirect(url_for('attendance.index'))
    return render_template('attendance/form.html', form=form, title='New Attendance Record' if current_user.role != 'student' else 'Submit Attendance')


@attendance_bp.route('/attendance/bulk', methods=['GET', 'POST'])
@login_required
@permission_required('attendance.create')
def bulk():
    if current_user.role != 'lecturer':
        flash('Bulk attendance is for lecturers.', 'warning')
        return redirect(url_for('attendance.index'))
    form = BulkAttendanceForm()
    form.unit_id.choices = [(u.id, f'{u.name} ({u.code})') for u in available_units_for_user()]
    unit_id = request.args.get('unit_id', type=int) or form.unit_id.data
    students = []
    if unit_id:
        unit = Unit.query.get(unit_id)
        if unit and lecturer_owns_unit(current_user, unit_id):
            students = Student.query.filter_by(program_id=unit.program_id).order_by(Student.first_name).all()
    while len(form.rows) < len(students):
        form.rows.append_entry()
    for row_form, student in zip(form.rows, students):
        row_form.student_id.data = student.id
        row_form.student_name.data = f'{student.full_name} - {student.admission_number}'
    if form.validate_on_submit() and students:
        if not lecturer_owns_unit(current_user, form.unit_id.data):
            flash('You can only mark attendance for your assigned units.', 'danger')
            return render_template('attendance/bulk_form.html', form=form, students=students)
        for row_form, student in zip(form.rows, students):
            existing = AttendanceRecord.query.filter_by(student_id=student.id, unit_id=form.unit_id.data, attendance_date=form.attendance_date.data).first()
            if existing:
                continue
            record = AttendanceRecord(student_id=student.id, unit_id=form.unit_id.data, attendance_date=form.attendance_date.data, status=row_form.status.data, source='lecturer', approval_status='approved', submitted_by_user_id=current_user.id, approved_by_user_id=current_user.id)
            db.session.add(record)
        db.session.commit()
        flash('Bulk attendance saved successfully.', 'success')
        return redirect(url_for('attendance.index'))
    return render_template('attendance/bulk_form.html', form=form, students=students)


@attendance_bp.route('/attendance/pending')
@login_required
@permission_required('attendance.approve')
def pending():
    records = AttendanceRecord.query.filter_by(approval_status='pending').order_by(AttendanceRecord.attendance_date.desc()).all()
    if current_user.role == 'lecturer':
        unit_ids = [item.unit_id for item in current_user.lecturer_units]
        records = [r for r in records if r.unit_id in unit_ids]
    return render_template('attendance/pending.html', records=records)


@attendance_bp.route('/attendance/<int:record_id>/approve', methods=['GET', 'POST'])
@login_required
@permission_required('attendance.approve')
def approve(record_id):
    record = AttendanceRecord.query.get_or_404(record_id)
    if current_user.role == 'lecturer' and not lecturer_owns_unit(current_user, record.unit_id):
        flash('You are not assigned to that unit.', 'danger')
        return redirect(url_for('attendance.index'))
    form = AttendanceApprovalForm()
    if form.validate_on_submit():
        record.approval_status = 'approved'
        record.approved_by_user_id = current_user.id
        db.session.commit()
        flash('Attendance approved.', 'success')
        return redirect(url_for('attendance.pending'))
    return render_template('attendance/approve.html', form=form, record=record)


@attendance_bp.route('/attendance/weekly-review')
@login_required
@permission_required('attendance.view')
def weekly_review():
    end_date = date.today(); start_date = end_date - timedelta(days=6)
    records = AttendanceRecord.query.filter(AttendanceRecord.attendance_date >= start_date, AttendanceRecord.attendance_date <= end_date).all()
    if current_user.role == 'lecturer':
        unit_ids = [item.unit_id for item in current_user.lecturer_units]
        records = [r for r in records if r.unit_id in unit_ids]
    elif current_user.role == 'student' and current_user.student_id:
        records = [r for r in records if r.student_id == current_user.student_id]
    summary = {}
    for record in records:
        key = record.student.full_name
        summary.setdefault(key, {'days_attended': 0, 'total_records': 0, 'pending': 0})
        summary[key]['total_records'] += 1
        if record.status == 'present' and record.approval_status == 'approved':
            summary[key]['days_attended'] += 1
        if record.approval_status == 'pending':
            summary[key]['pending'] += 1
    return render_template('attendance/weekly_review.html', summary=summary, start_date=start_date, end_date=end_date)
