from functools import wraps

from flask import abort, redirect, url_for
from flask_login import current_user

ROLE_PERMISSIONS = {
    'super_admin': {
        'users.manage', 'students.view', 'students.create', 'students.edit', 'students.delete',
        'admissions.view', 'admissions.create', 'admissions.edit', 'admissions.delete', 'admissions.approve',
        'finance.view', 'finance.create', 'finance.edit', 'finance.delete',
        'results.view', 'results.create', 'results.edit', 'results.delete', 'results.edit_own',
        'attendance.view', 'attendance.create', 'attendance.approve',
        'academics.view', 'academics.manage', 'dashboard.view', 'profile.manage', 'reports.view'
    },
    'registrar': {
        'students.view', 'students.create', 'students.edit',
        'admissions.view', 'admissions.create', 'admissions.edit', 'admissions.delete', 'admissions.approve',
        'academics.view', 'results.view', 'attendance.view', 'dashboard.view', 'profile.manage', 'reports.view'
    },
    'finance': {
        'students.view', 'finance.view', 'finance.create', 'finance.edit', 'finance.delete', 'dashboard.view', 'profile.manage', 'reports.view'
    },
    'lecturer': {
        'students.view', 'students.create', 'results.view', 'results.create', 'results.edit_own',
        'attendance.view', 'attendance.create', 'attendance.approve', 'dashboard.view', 'profile.manage'
    },
    'principal': {
        'students.view', 'admissions.view', 'finance.view', 'results.view', 'attendance.view', 'academics.view', 'dashboard.view', 'profile.manage', 'reports.view'
    },
    'student': {
        'attendance.create', 'dashboard.view', 'profile.manage'
    },
}

def has_permission(user, permission):
    if not user.is_authenticated:
        return False
    return permission in ROLE_PERMISSIONS.get(user.role, set())

def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not has_permission(current_user, permission):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

def lecturer_owns_unit(user, unit_id):
    if user.role != 'lecturer':
        return False
    return any(item.unit_id == unit_id for item in user.lecturer_units)
