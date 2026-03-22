from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models import (
    Application,
    AttendanceRecord,
    FeeInvoice,
    LecturerStudentAssignment,
    LecturerUnitAssignment,
    Payment,
    Program,
    ProgramAssessmentScheme,
    Result,
    Student,
    TimetableEntry,
    Unit,
    User,
)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'students': Student.query.count(),
        'applications': Application.query.count(),
        'programs': Program.query.count(),
        'units': Unit.query.count(),
        'invoices': FeeInvoice.query.count(),
        'payments': Payment.query.count(),
        'results': Result.query.count(),
        'users': User.query.count(),
        'revenue': sum(payment.amount for payment in Payment.query.all()),
        'outstanding': sum(invoice.balance for invoice in FeeInvoice.query.all()),
    }
    context = {}

    if current_user.role == 'super_admin':
        lecturers = User.query.filter_by(role='lecturer').order_by(User.full_name).all()
        students = Student.query.order_by(Student.id.desc()).all()
        pending_attendance = AttendanceRecord.query.filter_by(approval_status='pending').all()
        low_attendance = []
        for student in students:
            total = len(student.attendance_records)
            approved_present = len([x for x in student.attendance_records if x.approval_status == 'approved' and x.status == 'present'])
            pct = round((approved_present / total * 100), 2) if total else 0
            if total and pct < 75:
                low_attendance.append((student, pct))

        lecturers_without_units = [lect for lect in lecturers if not lect.lecturer_units]
        unassigned_students = [student for student in students if not student.lecturer_assignments]
        units_without_timetable = [unit for unit in Unit.query.all() if not unit.timetable_entries]
        programs_without_schemes = [program for program in Program.query.all() if not getattr(program, 'assessment_scheme_assignment', None)]
        inactive_users = User.query.filter_by(is_active_user=False).count()
        recent_students = students[:8]
        recent_payments = Payment.query.order_by(Payment.paid_at.desc()).limit(8).all()
        recent_applications = Application.query.order_by(Application.applied_at.desc()).limit(8).all()
        recent_results = Result.query.order_by(Result.created_at.desc()).limit(8).all()

        lecturer_rows = []
        for lecturer in lecturers:
            pending_for_lecturer = 0
            if lecturer.lecturer_units:
                unit_ids = [a.unit_id for a in lecturer.lecturer_units]
                pending_for_lecturer = AttendanceRecord.query.filter_by(approval_status='pending').filter(AttendanceRecord.unit_id.in_(unit_ids)).count()
            lecturer_rows.append({
                'lecturer': lecturer,
                'units_count': len(lecturer.lecturer_units),
                'students_count': len(lecturer.lecturer_students),
                'timetable_count': len(lecturer.timetable_entries),
                'results_count': Result.query.filter_by(entered_by=lecturer.id).count(),
                'pending_attendance': pending_for_lecturer,
            })

        context.update({
            'lecturers': lecturers,
            'lecturer_rows': lecturer_rows,
            'lecturer_count': len(lecturers),
            'lecturer_student_assignments': LecturerStudentAssignment.query.count(),
            'lecturer_unit_assignments': LecturerUnitAssignment.query.count(),
            'pending_attendance_count': len(pending_attendance),
            'lecturers_without_units_count': len(lecturers_without_units),
            'unassigned_students_count': len(unassigned_students),
            'units_without_timetable_count': len(units_without_timetable),
            'programs_without_schemes_count': len(programs_without_schemes),
            'inactive_users_count': inactive_users,
            'low_attendance_count': len(low_attendance),
            'low_attendance': low_attendance[:8],
            'recent_students': recent_students,
            'recent_payments': recent_payments,
            'recent_applications': recent_applications,
            'recent_results': recent_results,
            'today_classes': TimetableEntry.query.order_by(TimetableEntry.day_of_week, TimetableEntry.start_time).limit(8).all(),
        })

    elif current_user.role == 'lecturer':
        context['assigned_units'] = LecturerUnitAssignment.query.filter_by(lecturer_user_id=current_user.id).all()
        context['my_results_count'] = Result.query.filter_by(entered_by=current_user.id).count()
        context['my_students_count'] = Student.query.filter(Student.program_id.in_([a.unit.program_id for a in current_user.lecturer_units])).count() if current_user.lecturer_units else 0
        unit_ids = [item.unit_id for item in current_user.lecturer_units]
        context['pending_attendance'] = AttendanceRecord.query.filter_by(approval_status='pending').filter(AttendanceRecord.unit_id.in_(unit_ids)).count() if unit_ids else 0
        context['timetable'] = TimetableEntry.query.filter(TimetableEntry.lecturer_user_id == current_user.id).order_by(TimetableEntry.day_of_week, TimetableEntry.start_time).all()

    elif current_user.role == 'finance':
        context['today_collections'] = sum(payment.amount for payment in Payment.query.all())
        context['recent_payments'] = Payment.query.order_by(Payment.paid_at.desc()).limit(8).all()

    elif current_user.role == 'registrar':
        context['approved_applications'] = Application.query.filter_by(status='approved').count()
        context['recent_applications'] = Application.query.order_by(Application.applied_at.desc()).limit(8).all()

    elif current_user.role == 'student' and current_user.student_id:
        context['my_attendance'] = AttendanceRecord.query.filter_by(student_id=current_user.student_id).count()
        student = Student.query.get(current_user.student_id)
        context['timetable'] = TimetableEntry.query.join(Unit).filter(Unit.program_id == student.program_id).order_by(TimetableEntry.day_of_week, TimetableEntry.start_time).all() if student else []

    return render_template('dashboard.html', stats=stats, current_role=current_user.role, context=context)
