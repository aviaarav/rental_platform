from flask import Blueprint, render_template

from app.models import User
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = {
        'total_users': User.query.filter_by(role='user').count(),
        'blocked_users': User.query.filter_by(role='user', is_blocked=True).count(),
    }
    return render_template('admin/dashboard.html', stats=stats)