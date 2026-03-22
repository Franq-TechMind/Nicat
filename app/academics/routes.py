from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from app import db
from app.forms import AssessmentComponentForm, AssessmentSchemeForm, DepartmentForm, LecturerAssignmentForm, LecturerStudentAssignmentForm, ProgramForm, ProgramSchemeAssignForm, TimetableEntryForm, UnitForm
from app.models import AssessmentComponent, AssessmentScheme, Department, LecturerStudentAssignment, LecturerUnitAssignment, Program, ProgramAssessmentScheme, Result, Student, TimetableEntry, Unit, User
from app.utils import permission_required

academics_bp = Blueprint('academics', __name__)

def populate_departments(form):
    form.department_id.choices = [(d.id, f'{d.name} ({d.code})') for d in Department.query.order_by(Department.name).all()]

def populate_programs(form):
    form.program_id.choices = [(p.id, f'{p.name} ({p.code})') for p in Program.query.order_by(Program.name).all()]

def populate_schemes(form):
    form.scheme_id.choices = [(s.id, s.name) for s in AssessmentScheme.query.order_by(AssessmentScheme.name).all()]

def populate_lecturers(form):
    choices = [(u.id, u.full_name) for u in User.query.filter_by(role='lecturer', is_active_user=True).order_by(User.full_name).all()]
    if hasattr(form, 'lecturer_user_id'):
        form.lecturer_user_id.choices = choices

def populate_units(form):
    choices = [(u.id, f'{u.name} ({u.code})') for u in Unit.query.order_by(Unit.name).all()]
    if hasattr(form, 'unit_id'):
        form.unit_id.choices = choices

def populate_students(form):
    form.student_id.choices = [(s.id, f'{s.full_name} - {s.admission_number}') for s in Student.query.order_by(Student.first_name).all()]

@academics_bp.route('/academics')
@login_required
@permission_required('academics.view')
def index():
    departments = Department.query.order_by(Department.name).all()
    programs = Program.query.order_by(Program.name).all()
    units = Unit.query.order_by(Unit.name).all()
    schemes = AssessmentScheme.query.order_by(AssessmentScheme.name).all()
    assignments = ProgramAssessmentScheme.query.all()
    lecturer_assignments = LecturerUnitAssignment.query.all()
    lecturer_student_assignments = LecturerStudentAssignment.query.all()
    timetable_entries = TimetableEntry.query.order_by(TimetableEntry.day_of_week, TimetableEntry.start_time).all()
    return render_template('academics/index.html', departments=departments, programs=programs, units=units, schemes=schemes, assignments=assignments, lecturer_assignments=lecturer_assignments, lecturer_student_assignments=lecturer_student_assignments, timetable_entries=timetable_entries)

@academics_bp.route('/academics/lecturers/<int:lecturer_id>')
@login_required
@permission_required('academics.manage')
def lecturer_detail(lecturer_id):
    lecturer = User.query.filter_by(id=lecturer_id, role='lecturer').first_or_404()
    unit_assignments = LecturerUnitAssignment.query.filter_by(lecturer_user_id=lecturer.id).all()
    student_assignments = LecturerStudentAssignment.query.filter_by(lecturer_user_id=lecturer.id).all()
    timetable_entries = TimetableEntry.query.filter_by(lecturer_user_id=lecturer.id).order_by(TimetableEntry.day_of_week, TimetableEntry.start_time).all()
    results_count = Result.query.filter_by(entered_by=lecturer.id).count()
    return render_template('academics/lecturer_detail.html', lecturer=lecturer, unit_assignments=unit_assignments, student_assignments=student_assignments, timetable_entries=timetable_entries, results_count=results_count)

@academics_bp.route('/academics/departments/new', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(); form.populate_obj(department); db.session.add(department); db.session.commit(); flash('Department created.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/department_form.html', form=form, title='New Department')

@academics_bp.route('/academics/programs/new', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def create_program():
    form = ProgramForm(); populate_departments(form)
    if form.validate_on_submit():
        program = Program(); form.populate_obj(program); db.session.add(program); db.session.commit(); flash('Program created.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/program_form.html', form=form, title='New Program')

@academics_bp.route('/academics/units/new', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def create_unit():
    form = UnitForm(); populate_programs(form)
    if form.validate_on_submit():
        unit = Unit(); form.populate_obj(unit); db.session.add(unit); db.session.commit(); flash('Unit created.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/unit_form.html', form=form, title='New Unit')

@academics_bp.route('/academics/schemes/new', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def create_scheme():
    form = AssessmentSchemeForm()
    if form.validate_on_submit():
        scheme = AssessmentScheme(); form.populate_obj(scheme); db.session.add(scheme); db.session.commit(); flash('Assessment scheme created.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/scheme_form.html', form=form, title='New Assessment Scheme')

@academics_bp.route('/academics/schemes/<int:scheme_id>/components/new', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def create_scheme_component(scheme_id):
    scheme = AssessmentScheme.query.get_or_404(scheme_id); form = AssessmentComponentForm()
    if form.validate_on_submit():
        component = AssessmentComponent(scheme_id=scheme.id); form.populate_obj(component); db.session.add(component); db.session.commit(); flash('Assessment component added.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/component_form.html', form=form, title=f'New Component for {scheme.name}', scheme=scheme)

@academics_bp.route('/academics/schemes/assign', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def assign_scheme():
    form = ProgramSchemeAssignForm(); populate_programs(form); populate_schemes(form)
    if form.validate_on_submit():
        assignment = ProgramAssessmentScheme.query.filter_by(program_id=form.program_id.data).first()
        if not assignment:
            assignment = ProgramAssessmentScheme(program_id=form.program_id.data, scheme_id=form.scheme_id.data); db.session.add(assignment)
        else:
            assignment.scheme_id = form.scheme_id.data
        db.session.commit(); flash('Scheme assigned to program.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/assign_scheme_form.html', form=form, title='Assign Scheme to Program')

@academics_bp.route('/academics/lecturer-assignments/new', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def assign_lecturer_unit():
    form = LecturerAssignmentForm(); populate_lecturers(form); populate_units(form)
    if form.validate_on_submit():
        exists = LecturerUnitAssignment.query.filter_by(lecturer_user_id=form.lecturer_user_id.data, unit_id=form.unit_id.data).first()
        if exists:
            flash('That lecturer is already assigned to this unit.', 'warning')
        else:
            db.session.add(LecturerUnitAssignment(lecturer_user_id=form.lecturer_user_id.data, unit_id=form.unit_id.data)); db.session.commit(); flash('Lecturer assigned to unit.', 'success')
        return redirect(url_for('academics.index'))
    return render_template('academics/lecturer_assignment_form.html', form=form, title='Assign Lecturer to Unit')

@academics_bp.route('/academics/lecturer-assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@permission_required('academics.manage')
def remove_lecturer_unit_assignment(assignment_id):
    assignment = LecturerUnitAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment); db.session.commit(); flash('Lecturer-unit assignment removed.', 'info'); return redirect(url_for('academics.index'))

@academics_bp.route('/academics/lecturer-students/new', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def assign_student_to_lecturer():
    form = LecturerStudentAssignmentForm(); populate_lecturers(form); populate_students(form)
    if form.validate_on_submit():
        exists = LecturerStudentAssignment.query.filter_by(lecturer_user_id=form.lecturer_user_id.data, student_id=form.student_id.data).first()
        if exists:
            flash('That student is already assigned to this lecturer.', 'warning')
        else:
            db.session.add(LecturerStudentAssignment(lecturer_user_id=form.lecturer_user_id.data, student_id=form.student_id.data)); db.session.commit(); flash('Student assigned to lecturer.', 'success')
        return redirect(url_for('academics.index'))
    return render_template('academics/lecturer_student_assignment_form.html', form=form, title='Assign Student to Lecturer')

@academics_bp.route('/academics/lecturer-students/<int:assignment_id>/delete', methods=['POST'])
@login_required
@permission_required('academics.manage')
def remove_lecturer_student_assignment(assignment_id):
    assignment = LecturerStudentAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment); db.session.commit(); flash('Lecturer-student assignment removed.', 'info'); return redirect(url_for('academics.index'))

@academics_bp.route('/academics/timetable/new', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def create_timetable_entry():
    form = TimetableEntryForm(); populate_units(form); populate_lecturers(form)
    if form.validate_on_submit():
        entry = TimetableEntry(); form.populate_obj(entry); db.session.add(entry); db.session.commit(); flash('Timetable entry created.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/timetable_form.html', form=form, title='New Timetable Entry')

@academics_bp.route('/academics/departments/<int:department_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def edit_department(department_id):
    department = Department.query.get_or_404(department_id)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        form.populate_obj(department); db.session.commit(); flash('Department updated.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/department_form.html', form=form, title='Edit Department')

@academics_bp.route('/academics/programs/<int:program_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def edit_program(program_id):
    program = Program.query.get_or_404(program_id)
    form = ProgramForm(obj=program); populate_departments(form)
    if form.validate_on_submit():
        form.populate_obj(program); db.session.commit(); flash('Program updated.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/program_form.html', form=form, title='Edit Program')

@academics_bp.route('/academics/units/<int:unit_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def edit_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    form = UnitForm(obj=unit); populate_programs(form)
    if form.validate_on_submit():
        form.populate_obj(unit); db.session.commit(); flash('Unit updated.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/unit_form.html', form=form, title='Edit Unit')

@academics_bp.route('/academics/schemes/<int:scheme_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def edit_scheme(scheme_id):
    scheme = AssessmentScheme.query.get_or_404(scheme_id)
    form = AssessmentSchemeForm(obj=scheme)
    if form.validate_on_submit():
        form.populate_obj(scheme); db.session.commit(); flash('Assessment scheme updated.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/scheme_form.html', form=form, title='Edit Assessment Scheme')

@academics_bp.route('/academics/timetable/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('academics.manage')
def edit_timetable_entry(entry_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    form = TimetableEntryForm(obj=entry); populate_units(form); populate_lecturers(form)
    if form.validate_on_submit():
        form.populate_obj(entry); db.session.commit(); flash('Timetable entry updated.', 'success'); return redirect(url_for('academics.index'))
    return render_template('academics/timetable_form.html', form=form, title='Edit Timetable Entry')

@academics_bp.route('/academics/departments/<int:department_id>/delete', methods=['POST'])
@login_required
@permission_required('academics.manage')
def delete_department(department_id):
    department = Department.query.get_or_404(department_id)
    db.session.delete(department); db.session.commit(); flash('Department deleted.', 'info'); return redirect(url_for('academics.index'))

@academics_bp.route('/academics/programs/<int:program_id>/delete', methods=['POST'])
@login_required
@permission_required('academics.manage')
def delete_program(program_id):
    program = Program.query.get_or_404(program_id)
    db.session.delete(program); db.session.commit(); flash('Program deleted.', 'info'); return redirect(url_for('academics.index'))

@academics_bp.route('/academics/units/<int:unit_id>/delete', methods=['POST'])
@login_required
@permission_required('academics.manage')
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    db.session.delete(unit); db.session.commit(); flash('Unit deleted.', 'info'); return redirect(url_for('academics.index'))

@academics_bp.route('/academics/schemes/<int:scheme_id>/delete', methods=['POST'])
@login_required
@permission_required('academics.manage')
def delete_scheme(scheme_id):
    scheme = AssessmentScheme.query.get_or_404(scheme_id)
    db.session.delete(scheme); db.session.commit(); flash('Assessment scheme deleted.', 'info'); return redirect(url_for('academics.index'))

@academics_bp.route('/academics/timetable/<int:entry_id>/delete', methods=['POST'])
@login_required
@permission_required('academics.manage')
def delete_timetable_entry(entry_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    db.session.delete(entry); db.session.commit(); flash('Timetable entry deleted.', 'info'); return redirect(url_for('academics.index'))
