from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    stats = {
        'resources': current_user.resources.count(),
        'received': current_user.bookings_received.count(),
        'sent': current_user.bookings_made.count(),
    }
    return render_template('dashboard.html', stats=stats)