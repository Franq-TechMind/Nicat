from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.forms import ApplicationForm, ApproveApplicationForm
from app.models import Application, Program, Student
from app.utils import permission_required

admissions_bp = Blueprint('admissions', __name__)


def populate_programs(form):
    form.program_id.choices = [(p.id, f'{p.name} ({p.code})') for p in Program.query.order_by(Program.name).all()]


def split_name(full_name):
    bits = full_name.strip().split()
    if not bits:
        return '', ''
    if len(bits) == 1:
        return bits[0], bits[0]
    return bits[0], ' '.join(bits[1:])


@admissions_bp.route('/admissions')
@login_required
@permission_required('admissions.view')
def index():
    q = request.args.get('q', '').strip()
    query = Application.query
    if q:
        query = query.filter(Application.applicant_name.ilike(f'%{q}%') | Application.application_number.ilike(f'%{q}%'))
    applications = query.order_by(Application.id.desc()).all()
    return render_template('admissions/index.html', applications=applications, q=q)


@admissions_bp.route('/admissions/new', methods=['GET', 'POST'])
@login_required
@permission_required('admissions.create')
def create():
    form = ApplicationForm()
    populate_programs(form)
    if form.validate_on_submit():
        application = Application(
            application_number=form.application_number.data,
            applicant_name=form.applicant_name.data,
            email=form.email.data.lower() if form.email.data else None,
            phone=form.phone.data,
            status=form.status.data,
            program_id=form.program_id.data,
        )
        db.session.add(application)
        db.session.commit()
        flash('Application created successfully.', 'success')
        return redirect(url_for('admissions.index'))
    return render_template('admissions/form.html', form=form, title='New Application')


@admissions_bp.route('/admissions/<int:application_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('admissions.edit')
def edit(application_id):
    application = Application.query.get_or_404(application_id)
    form = ApplicationForm(obj=application)
    populate_programs(form)
    if form.validate_on_submit():
        form.populate_obj(application)
        application.email = application.email.lower() if application.email else None
        db.session.commit()
        flash('Application updated successfully.', 'success')
        return redirect(url_for('admissions.index'))
    return render_template('admissions/form.html', form=form, title='Edit Application')


@admissions_bp.route('/admissions/<int:application_id>/approve', methods=['GET', 'POST'])
@login_required
@permission_required('admissions.edit')
def approve(application_id):
    application = Application.query.get_or_404(application_id)
    if application.student_id:
        flash('This application is already linked to a student record.', 'warning')
        return redirect(url_for('admissions.index'))

    first_name, last_name = split_name(application.applicant_name)
    form = ApproveApplicationForm(
        admission_number=f"NICAT-{application.id:04d}",
        first_name=first_name,
        last_name=last_name,
        send_portal_ready_note=True,
    )

    if form.validate_on_submit():
        if Student.query.filter_by(admission_number=form.admission_number.data).first():
            flash('That admission number already exists.', 'danger')
            return render_template('admissions/approve.html', form=form, application=application)
        if application.email and Student.query.filter_by(email=application.email.lower()).first():
            flash('A student with that email already exists.', 'danger')
            return render_template('admissions/approve.html', form=form, application=application)

        student = Student(
            admission_number=form.admission_number.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=application.phone,
            email=application.email.lower() if application.email else None,
            status='active',
            program_id=application.program_id,
            portal_ready=form.send_portal_ready_note.data,
        )
        db.session.add(student)
        db.session.flush()

        application.status = 'approved'
        application.student_id = student.id
        db.session.commit()
        flash('Application approved and student record created.', 'success')
        return redirect(url_for('students.index'))

    return render_template('admissions/approve.html', form=form, application=application)


@admissions_bp.route('/admissions/<int:application_id>/delete', methods=['POST'])
@login_required
@permission_required('admissions.delete')
def delete(application_id):
    application = Application.query.get_or_404(application_id)
    db.session.delete(application)
    db.session.commit()
    flash('Application deleted.', 'info')
    return redirect(url_for('admissions.index'))
