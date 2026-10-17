from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(view):
    """Allow only logged-in users whose role is 'admin'."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in as administrator.', 'warning')
            return redirect(url_for('auth.admin_login'))
        if not current_user.is_admin:
            flash('You are not authorized to open the admin area.', 'danger')
            return redirect(url_for('dashboard.index'))
        return view(*args, **kwargs)
    return wrapped