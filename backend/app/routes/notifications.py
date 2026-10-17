"""In-app notifications: list, mark read, and a small JSON feed for the navbar badge and popups."""
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.app_context_processor
def inject_unread_count():
    """`unread_count` is available in every template for the navbar badge."""
    if current_user.is_authenticated:
        return {'unread_count': current_user.notifications.filter_by(is_read=False).count()}
    return {'unread_count': 0}


def _safe_link(link):
    """Only follow the relative links this app stores; never an external URL."""
    return link if link and link.startswith('/') and not link.startswith('//') else url_for('notifications.index')


@notifications_bp.route('')
@login_required
def index():
    items = current_user.notifications.order_by(Notification.created_at.desc()).limit(100).all()
    return render_template('notifications/index.html', items=items)


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark one notification read and open its link."""
    item = db.session.get(Notification, notification_id)
    if item is None or item.user_id != current_user.id:
        abort(404)
    item.is_read = True
    db.session.commit()
    return redirect(_safe_link(item.link))


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    current_user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/unread.json')
@login_required
def unread():
    """Count plus the five newest unread notifications; polled by static/js/notifications.js."""
    query = current_user.notifications.filter_by(is_read=False)
    items = query.order_by(Notification.created_at.desc()).limit(5).all()
    return jsonify(count=query.count(), items=[
        {'id': n.id, 'title': n.title, 'message': n.message,
         'link': url_for('notifications.mark_read', notification_id=n.id),
         'created_at': n.created_at.isoformat()} for n in items])
