from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.forms import (
    ChangePasswordForm,
    LecturerProfileForm,
    LoginForm,
    PasswordResetForm,
    ProfileForm,
    RegisterAdminForm,
    StudentSignupForm,
    UserEditForm,
    UserForm,
)
from app.models import Student, User
from app.utils import permission_required

auth_bp = Blueprint('auth', __name__)


def role_dashboard(role):
    if role == 'student':
        return 'students.portal'
    return 'main.dashboard'


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(role_dashboard(current_user.role)))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data) and user.is_active_user:
            login_user(user)
            flash('Welcome back.', 'success')
            return redirect(url_for(role_dashboard(user.role)))
        flash('Invalid credentials or inactive account.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register-admin', methods=['GET', 'POST'])
def register_admin():
    existing_super = User.query.filter_by(role='super_admin').first()
    if existing_super:
        flash('Super admin already exists. Please sign in.', 'warning')
        return redirect(url_for('auth.login'))
    form = RegisterAdminForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash('That email is already in use.', 'danger')
            return render_template('auth/register_admin.html', form=form)
        user = User(full_name=form.full_name.data, email=form.email.data.lower(), role='super_admin', is_active_user=True)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Super admin account created. Please sign in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_admin.html', form=form)


@auth_bp.route('/student-signup', methods=['GET', 'POST'])
def student_signup():
    if current_user.is_authenticated:
        return redirect(url_for(role_dashboard(current_user.role)))
    form = StudentSignupForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        student = Student.query.filter_by(admission_number=form.admission_number.data, email=email).first()
        if not student:
            flash('No matching approved student record was found for that admission number and email.', 'danger')
            return render_template('auth/student_signup.html', form=form)
        existing_user = User.query.filter((User.email == email) | (User.student_id == student.id)).first()
        if existing_user:
            flash('A user account already exists for this student.', 'warning')
            return redirect(url_for('auth.login'))
        user = User(full_name=student.full_name, email=email, role='student', is_active_user=True, student_id=student.id)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Student account created successfully. Please sign in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/student_signup.html', form=form)


@auth_bp.route('/users')
@login_required
@permission_required('users.manage')
def users():
    users = User.query.order_by(User.role, User.full_name).all()
    return render_template('auth/users.html', users=users)


@auth_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@permission_required('users.manage')
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('That email is already in use.', 'danger')
            return render_template('auth/user_form.html', form=form, title='Create User')
        student_id = None
        if form.role.data == 'student':
            student = Student.query.filter_by(email=email).first()
            if not student:
                flash('To create a student user manually, first create the student record with the same email.', 'warning')
                return render_template('auth/user_form.html', form=form, title='Create User')
            student_id = student.id
        user = User(full_name=form.full_name.data, email=email, role=form.role.data, is_active_user=form.is_active_user.data, student_id=student_id)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User account created.', 'success')
        return redirect(url_for('auth.users'))
    return render_template('auth/user_form.html', form=form, title='Create User')


@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('users.manage')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'super_admin':
        flash('Super admin role cannot be edited here.', 'warning')
        return redirect(url_for('auth.users'))
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        email = form.email.data.lower()
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            flash('That email is already in use.', 'danger')
            return render_template('auth/user_edit_form.html', form=form, title='Edit User', user=user)
        user.full_name = form.full_name.data
        user.email = email
        user.role = form.role.data
        user.is_active_user = form.is_active_user.data
        if user.role == 'student':
            student = Student.query.filter_by(email=email).first()
            user.student_id = student.id if student else None
        else:
            user.student_id = None
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('auth.users'))
    return render_template('auth/user_edit_form.html', form=form, title='Edit User', user=user)


@auth_bp.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@permission_required('users.manage')
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Password reset successfully.', 'success')
        return redirect(url_for('auth.users'))
    return render_template('auth/reset_password.html', form=form, user=user)


@auth_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@permission_required('users.manage')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'super_admin':
        flash('Super admin cannot be deactivated here.', 'warning')
        return redirect(url_for('auth.users'))
    user.is_active_user = not user.is_active_user
    db.session.commit()
    flash('User status updated.', 'success')
    return redirect(url_for('auth.users'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@permission_required('profile.manage')
def profile():
    if current_user.role == 'lecturer':
        form = LecturerProfileForm(full_name=current_user.full_name, email=current_user.email, staff_id=current_user.staff_id, phone=current_user.phone, department_name=current_user.department_name, specialization=current_user.specialization)
    else:
        form = ProfileForm(full_name=current_user.full_name, email=current_user.email)
    password_form = ChangePasswordForm()
    if form.submit.data and form.validate_on_submit():
        email = form.email.data.lower()
        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            flash('That email is already in use.', 'danger')
            return render_template('auth/profile.html', form=form, password_form=password_form)
        current_user.full_name = form.full_name.data
        current_user.email = email
        if current_user.role == 'lecturer':
            current_user.staff_id = form.staff_id.data
            current_user.phone = form.phone.data
            current_user.department_name = form.department_name.data
            current_user.specialization = form.specialization.data
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html', form=form, password_form=password_form)


@auth_bp.route('/change-password', methods=['POST'])
@login_required
@permission_required('profile.manage')
def change_password():
    if current_user.role == 'lecturer':
        form = LecturerProfileForm(full_name=current_user.full_name, email=current_user.email, staff_id=current_user.staff_id, phone=current_user.phone, department_name=current_user.department_name, specialization=current_user.specialization)
    else:
        form = ProfileForm(full_name=current_user.full_name, email=current_user.email)
    password_form = ChangePasswordForm()
    if password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/profile.html', form=form, password_form=password_form)
        current_user.set_password(password_form.new_password.data)
        db.session.commit()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html', form=form, password_form=password_form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('auth.login'))
