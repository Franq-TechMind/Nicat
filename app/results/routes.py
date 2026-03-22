from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import ModuleBasedResultForm, ResultForm
from app.models import AssessmentScheme, ModuleComponentScore, ModuleResult, ProgramAssessmentScheme, Result, Semester, Student, Unit
from app.utils import lecturer_owns_unit, permission_required

results_bp = Blueprint('results', __name__)


def calculate_grade(score):
    if score >= 70:
        return 'A', 'Pass'
    if score >= 60:
        return 'B', 'Pass'
    if score >= 50:
        return 'C', 'Pass'
    if score >= 40:
        return 'D', 'Supplementary'
    return 'E', 'Fail'


def available_units_for_user():
    if current_user.role == 'lecturer':
        assigned_ids = [item.unit_id for item in current_user.lecturer_units]
        return Unit.query.filter(Unit.id.in_(assigned_ids)).order_by(Unit.name).all() if assigned_ids else []
    return Unit.query.order_by(Unit.name).all()


def available_students_for_user():
    if current_user.role == 'lecturer':
        explicit_student_ids = [item.student_id for item in current_user.lecturer_students]
        program_ids = list({item.unit.program_id for item in current_user.lecturer_units})
        query = Student.query
        if explicit_student_ids:
            query = query.filter((Student.id.in_(explicit_student_ids)) | (Student.program_id.in_(program_ids)))
        elif program_ids:
            query = query.filter(Student.program_id.in_(program_ids))
        else:
            return []
        return query.order_by(Student.first_name).all()
    return Student.query.order_by(Student.first_name).all()


def populate_choices(form):
    form.student_id.choices = [(s.id, f'{s.full_name} - {s.admission_number}') for s in available_students_for_user()]
    form.unit_id.choices = [(u.id, f'{u.name} ({u.code})') for u in available_units_for_user()]
    form.semester_id.choices = [(s.id, f'{s.name} - {s.academic_year.name}') for s in Semester.query.order_by(Semester.id.desc()).all()]


def _flash_errors(field_label, errors):
    if isinstance(errors, (list, tuple)):
        for error in errors:
            if isinstance(error, (list, tuple, dict)):
                _flash_errors(field_label, error)
            else:
                flash(f'{field_label}: {error}', 'danger')
    elif isinstance(errors, dict):
        for subfield, suberrors in errors.items():
            _flash_errors(f"{field_label} / {subfield.replace('_', ' ').title()}", suberrors)
    else:
        flash(f'{field_label}: {errors}', 'danger')


def flash_form_errors(form):
    for field_name, errors in form.errors.items():
        field = getattr(form, field_name, None)
        label = getattr(field, 'label', None)
        base_label = label.text if label else field_name.replace('_', ' ').title()
        _flash_errors(base_label, errors)


def get_program_scheme_for_student(student_id):
    student = Student.query.get_or_404(student_id)
    program_link = ProgramAssessmentScheme.query.filter_by(program_id=student.program_id).first()
    if not program_link:
        return student, None, None
    scheme = AssessmentScheme.query.get(program_link.scheme_id)
    return student, program_link, scheme


def validate_module_input(form):
    modules = [form.module_1, form.module_2, form.module_3]
    has_any = False
    for idx, module in enumerate(modules, start=1):
        cat = module.cat.data or 0
        group_work = module.group_work.data or 0
        final_exam = module.final_exam.data or 0
        if any(v > 0 for v in [cat, group_work, final_exam]):
            has_any = True
        if cat > 30:
            return False, f'Module {idx} CAT cannot exceed 30.'
        if group_work > 20:
            return False, f'Module {idx} Group Work cannot exceed 20.'
        if final_exam > 60:
            return False, f'Module {idx} Final Exam cannot exceed 60.'
    if not has_any:
        return False, 'Enter marks for at least one module before saving.'
    return True, None


def apply_module_result_update(result, form):
    student, program_link, scheme = get_program_scheme_for_student(form.student_id.data)
    if not program_link or not scheme:
        return False, 'No assessment scheme is assigned to this student program yet.'
    if scheme.module_count != 3:
        return False, 'This result screen currently supports 3-module assessment schemes only.'
    components = {c.name.lower().replace(' ', '_'): c for c in sorted(scheme.components, key=lambda x: x.position)}
    if not {'cat', 'group_work', 'final_exam'}.issubset(set(components.keys())):
        return False, 'The assigned assessment scheme is missing CAT, Group Work, or Final Exam components.'

    result.student_id = form.student_id.data
    result.unit_id = form.unit_id.data
    result.semester_id = form.semester_id.data
    result.entered_by = current_user.id if current_user.role == 'lecturer' else result.entered_by

    module_entries = [form.module_1.data, form.module_2.data, form.module_3.data]
    existing_modules = {m.module_number: m for m in result.module_results}
    overall_converted = 0

    for idx, entry in enumerate(module_entries, start=1):
        cat = float(entry.get('cat') or 0)
        group_work = float(entry.get('group_work') or 0)
        final_exam = float(entry.get('final_exam') or 0)
        raw_total = cat + group_work + final_exam
        converted_total = round((raw_total / scheme.raw_total) * scheme.converted_total, 2) if scheme.raw_total else raw_total
        grade, remarks = calculate_grade(converted_total)
        overall_converted += converted_total

        module_result = existing_modules.get(idx)
        if not module_result:
            module_result = ModuleResult(result_id=result.id, module_number=idx)
            db.session.add(module_result)
            db.session.flush()

        module_result.raw_total = raw_total
        module_result.converted_total = converted_total
        module_result.grade = grade
        module_result.remarks = remarks

        score_map = {s.component_name: s for s in module_result.component_scores}
        for component_name, value, key in [('CAT', cat, 'cat'), ('Group Work', group_work, 'group_work'), ('Final Exam', final_exam, 'final_exam')]:
            component_score = score_map.get(component_name)
            if not component_score:
                component_score = ModuleComponentScore(module_result_id=module_result.id, component_name=component_name, max_marks=components[key].max_marks, score=value)
                db.session.add(component_score)
            else:
                component_score.max_marks = components[key].max_marks
                component_score.score = value

    overall_mark = round(overall_converted / scheme.module_count, 2)
    final_grade, final_remarks = calculate_grade(overall_mark)
    result.marks = overall_mark
    result.grade = final_grade
    result.remarks = final_remarks
    return True, None


@results_bp.route('/results')
@login_required
@permission_required('results.view')
def index():
    results = Result.query.order_by(Result.id.desc()).all()
    if current_user.role == 'lecturer':
        unit_ids = [item.unit_id for item in current_user.lecturer_units]
        results = [r for r in results if r.unit_id in unit_ids]
    return render_template('results/index.html', results=results)


@results_bp.route('/results/new', methods=['GET', 'POST'])
@login_required
@permission_required('results.create')
def create():
    form = ResultForm()
    populate_choices(form)
    if form.validate_on_submit():
        if current_user.role == 'lecturer' and not lecturer_owns_unit(current_user, form.unit_id.data):
            flash('You can only enter results for your assigned units.', 'danger')
            return render_template('results/form.html', form=form, title='New Result')
        result = Result(entered_by=current_user.id)
        form.populate_obj(result)
        db.session.add(result)
        db.session.commit()
        flash('Result created successfully.', 'success')
        return redirect(url_for('results.index'))
    elif form.is_submitted():
        flash_form_errors(form)
    return render_template('results/form.html', form=form, title='New Result')


@results_bp.route('/results/module-based/new', methods=['GET', 'POST'])
@login_required
@permission_required('results.create')
def create_module_based():
    form = ModuleBasedResultForm()
    populate_choices(form)
    if not form.student_id.choices:
        flash('No students are available for result capture yet.', 'warning')
    if not form.unit_id.choices:
        flash('No units are available for result capture yet.', 'warning')
    if form.validate_on_submit():
        if current_user.role == 'lecturer' and not lecturer_owns_unit(current_user, form.unit_id.data):
            flash('You can only enter results for your assigned units.', 'danger')
            return render_template('results/module_form.html', form=form, title='New Module Result')
        ok, error = validate_module_input(form)
        if not ok:
            flash(error, 'danger')
            return render_template('results/module_form.html', form=form, title='New Module Result')
        existing_result = Result.query.filter_by(student_id=form.student_id.data, unit_id=form.unit_id.data, semester_id=form.semester_id.data).first()
        if existing_result:
            if existing_result.module_results:
                flash('A module-based result for this student, unit and semester already exists. You can edit it instead.', 'warning')
                return redirect(url_for('results.edit_module_based', result_id=existing_result.id))
            flash('A standard result already exists for this student, unit and semester. Edit or delete it first.', 'warning')
            return redirect(url_for('results.edit', result_id=existing_result.id))
        result = Result(student_id=form.student_id.data, unit_id=form.unit_id.data, semester_id=form.semester_id.data, marks=0, grade='E', remarks='Pending Review', entered_by=current_user.id)
        db.session.add(result)
        db.session.flush()
        ok, error = apply_module_result_update(result, form)
        if not ok:
            db.session.rollback()
            flash(error, 'danger')
            return render_template('results/module_form.html', form=form, title='New Module Result')
        db.session.commit()
        flash('Module-based results saved successfully. Each module has been stored separately under this result record.', 'success')
        return redirect(url_for('results.detail', result_id=result.id))
    elif form.is_submitted():
        flash_form_errors(form)
    return render_template('results/module_form.html', form=form, title='New Module Result')


@results_bp.route('/results/module-based/<int:result_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('results.edit_own')
def edit_module_based(result_id):
    result = Result.query.get_or_404(result_id)
    if not result.module_results:
        flash('This is not a module-based result.', 'warning')
        return redirect(url_for('results.edit', result_id=result.id))
    if current_user.role == 'lecturer' and result.entered_by != current_user.id:
        flash('You can only edit module-based results you entered.', 'danger')
        return redirect(url_for('results.index'))
    if current_user.role == 'lecturer' and not lecturer_owns_unit(current_user, result.unit_id):
        flash('You can only edit results for your assigned units.', 'danger')
        return redirect(url_for('results.index'))

    form = ModuleBasedResultForm()
    populate_choices(form)

    if not form.is_submitted():
        form.student_id.data = result.student_id
        form.unit_id.data = result.unit_id
        form.semester_id.data = result.semester_id
        for module in result.module_results:
            scores = {s.component_name: s.score for s in module.component_scores}
            target = getattr(form, f'module_{module.module_number}')
            target.cat.data = scores.get('CAT', 0)
            target.group_work.data = scores.get('Group Work', 0)
            target.final_exam.data = scores.get('Final Exam', 0)

    if form.validate_on_submit():
        if current_user.role == 'lecturer' and not lecturer_owns_unit(current_user, form.unit_id.data):
            flash('You can only edit results for your assigned units.', 'danger')
            return render_template('results/module_form.html', form=form, title='Edit Module Result')
        ok, error = validate_module_input(form)
        if not ok:
            flash(error, 'danger')
            return render_template('results/module_form.html', form=form, title='Edit Module Result')
        conflicting = Result.query.filter(Result.student_id == form.student_id.data, Result.unit_id == form.unit_id.data, Result.semester_id == form.semester_id.data, Result.id != result.id).first()
        if conflicting:
            flash('Another result already exists for this student, unit and semester.', 'warning')
            return render_template('results/module_form.html', form=form, title='Edit Module Result')
        ok, error = apply_module_result_update(result, form)
        if not ok:
            flash(error, 'danger')
            return render_template('results/module_form.html', form=form, title='Edit Module Result')
        db.session.commit()
        flash('Module-based result updated successfully.', 'success')
        return redirect(url_for('results.index'))
    elif form.is_submitted():
        flash_form_errors(form)

    return render_template('results/module_form.html', form=form, title='Edit Module Result')


@results_bp.route('/results/<int:result_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('results.edit_own')
def edit(result_id):
    result = Result.query.get_or_404(result_id)
    if current_user.role == 'lecturer' and result.entered_by != current_user.id:
        flash('You can only edit results you entered.', 'danger')
        return redirect(url_for('results.index'))
    if result.module_results:
        return redirect(url_for('results.edit_module_based', result_id=result.id))
    form = ResultForm(obj=result)
    populate_choices(form)
    if form.validate_on_submit():
        form.populate_obj(result)
        db.session.commit()
        flash('Result updated successfully.', 'success')
        return redirect(url_for('results.index'))
    elif form.is_submitted():
        flash_form_errors(form)
    return render_template('results/form.html', form=form, title='Edit Result')


@results_bp.route('/results/<int:result_id>')
@login_required
@permission_required('results.view')
def detail(result_id):
    result = Result.query.get_or_404(result_id)
    if current_user.role == 'lecturer' and not lecturer_owns_unit(current_user, result.unit_id):
        flash('You are not assigned to that unit.', 'danger')
        return redirect(url_for('results.index'))
    return render_template('results/detail.html', result=result)


@results_bp.route('/results/<int:result_id>/delete', methods=['POST'])
@login_required
@permission_required('results.edit_own')
def delete(result_id):
    result = Result.query.get_or_404(result_id)
    if current_user.role == 'lecturer' and result.entered_by != current_user.id:
        flash('You can only delete results you entered.', 'danger')
        return redirect(url_for('results.index'))
    db.session.delete(result)
    db.session.commit()
    flash('Result deleted.', 'info')
    return redirect(url_for('results.index'))
