from flask import Blueprint, render_template, request
from flask_login import login_required

from app.forms import LecturerFilterForm
from app.models import AttendanceRecord, LecturerStudentAssignment, LecturerUnitAssignment, Result, TimetableEntry, User
from app.utils import permission_required

lecturers_bp = Blueprint('lecturers', __name__)


@lecturers_bp.route('/lecturers')
@login_required
@permission_required('academics.manage')
def index():
    q = request.args.get('q', '').strip()
    department_name = request.args.get('department_name', '').strip()
    status = request.args.get('status', '').strip()

    form = LecturerFilterForm(q=q, department_name=department_name, status=status)
    query = User.query.filter_by(role='lecturer')

    if q:
        query = query.filter((User.full_name.ilike(f'%{q}%')) | (User.email.ilike(f'%{q}%')) | (User.staff_id.ilike(f'%{q}%')))
    if department_name:
        query = query.filter(User.department_name.ilike(f'%{department_name}%'))
    if status == 'active':
        query = query.filter_by(is_active_user=True)
    elif status == 'inactive':
        query = query.filter_by(is_active_user=False)

    lecturers = query.order_by(User.full_name).all()
    lecturer_rows = []
    for lecturer in lecturers:
        unit_ids = [a.unit_id for a in lecturer.lecturer_units]
        pending_attendance = AttendanceRecord.query.filter_by(approval_status='pending').filter(AttendanceRecord.unit_id.in_(unit_ids)).count() if unit_ids else 0
        lecturer_rows.append({
            'lecturer': lecturer,
            'units_count': len(lecturer.lecturer_units),
            'students_count': len(lecturer.lecturer_students),
            'timetable_count': len(lecturer.timetable_entries),
            'results_count': Result.query.filter_by(entered_by=lecturer.id).count(),
            'pending_attendance': pending_attendance,
        })

    summary = {
        'lecturers': len(lecturers),
        'unit_assignments': LecturerUnitAssignment.query.count(),
        'student_assignments': LecturerStudentAssignment.query.count(),
        'timetable_entries': TimetableEntry.query.count(),
    }
    return render_template('lecturers/index.html', form=form, lecturer_rows=lecturer_rows, summary=summary)
