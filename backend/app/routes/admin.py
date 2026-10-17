"""Admin area: overview, users (block / unblock), listings (hide / unhide), bookings and activity logs."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, or_

from app.constants import (
    ROLE_USER,
    STATUS_APPROVED,
    STATUS_BORROWED,
    STATUS_CANCELLED,
    STATUS_PENDING,
    STATUS_REJECTED,
    STATUS_RETURNED,
    TYPE_EQUIPMENT,
    TYPE_PROFESSIONAL,
)
from app.extensions import db
from app.models import ActivityLog, BookingRequest, Resource, Review, User
from app.services.notify import create_notification, log_activity
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

PER_PAGE = 20
LOGS_PER_PAGE = 50
STATUSES = [STATUS_PENDING, STATUS_APPROVED, STATUS_BORROWED, STATUS_RETURNED, STATUS_REJECTED, STATUS_CANCELLED]


# ---------- helpers ----------

def _page():
    raw = request.args.get('page', '1')
    return int(raw) if raw.isdigit() and int(raw) > 0 else 1


def _page_args():
    """Current filters without `page`, so pagination links keep them."""
    return {k: v for k, v in request.args.items() if v and k != 'page'}


def _paginate(query, per_page=PER_PAGE):
    return query.paginate(page=_page(), per_page=per_page, error_out=False)


def _next_url(fallback):
    """Where to go after a POST action: the page it was sent from, if it is one of ours."""
    target = request.form.get('next', '')
    return target if target.startswith('/') and not target.startswith('//') else fallback


def _member(user_id):
    """A non-admin user or 404. Admin accounts are never managed from here."""
    user = db.session.get(User, user_id)
    if user is None or user.is_admin:
        abort(404)
    return user


def _booking_counts():
    rows = (db.session.query(func.lower(func.trim(BookingRequest.status)), func.count(BookingRequest.id))
            .group_by(func.lower(func.trim(BookingRequest.status))).all())
    found = dict(rows)
    return {status: found.get(status.lower(), 0) for status in STATUSES}


# ---------- dashboard ----------

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = {
        'total_users': User.query.filter_by(role=ROLE_USER).count(),
        'blocked_users': User.query.filter_by(role=ROLE_USER, is_blocked=True).count(),
        'total_resources': Resource.query.count(),
        'hidden_resources': Resource.query.filter_by(is_hidden=True).count(),
        'equipment': Resource.query.filter_by(resource_type=TYPE_EQUIPMENT).count(),
        'services': Resource.query.filter_by(resource_type=TYPE_PROFESSIONAL).count(),
        'total_bookings': BookingRequest.query.count(),
        'reviews': Review.query.count(),
    }
    recent_bookings = BookingRequest.query.order_by(BookingRequest.created_at.desc()).limit(5).all()
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    return render_template('admin/dashboard.html', stats=stats, booking_counts=_booking_counts(),
                           recent_bookings=recent_bookings, recent_logs=recent_logs)


# ---------- users ----------

@admin_bp.route('/users')
@admin_required
def users():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()

    query = User.query.filter_by(role=ROLE_USER)
    if q:
        like = f'%{q}%'
        query = query.filter(or_(User.full_name.ilike(like), User.email.ilike(like), User.phone.ilike(like)))
    if status == 'blocked':
        query = query.filter(User.is_blocked.is_(True))
    elif status == 'active':
        query = query.filter(User.is_blocked.is_(False))
    else:
        status = ''

    pagination = _paginate(query.order_by(User.created_at.desc()))
    return render_template('admin/users.html', pagination=pagination, users=pagination.items,
                           q=q, status=status, page_args=_page_args())


@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    user = _member(user_id)
    return render_template(
        'admin/user_detail.html', user=user,
        listings=user.resources.order_by(Resource.created_at.desc()).all(),
        bookings_made=user.bookings_made.order_by(BookingRequest.created_at.desc()).limit(10).all(),
        bookings_received=user.bookings_received.order_by(BookingRequest.created_at.desc()).limit(10).all(),
        logs=user.activities.order_by(ActivityLog.created_at.desc()).limit(10).all())


@admin_bp.route('/users/<int:user_id>/<action>', methods=['POST'])
@admin_required
def set_blocked(user_id, action):
    """Block or unblock a user. A blocked user is logged out on their next request."""
    if action not in ('block', 'unblock'):
        abort(404)
    user = _member(user_id)
    user.is_blocked = action == 'block'
    db.session.commit()
    log_activity(f'User {action}ed', f'{user.full_name} ({user.email})', user_id=current_user.id)
    flash(f'{user.full_name} has been {action}ed.', 'success' if action == 'unblock' else 'warning')
    return redirect(_next_url(url_for('admin.user_detail', user_id=user.id)))


# ---------- resources ----------

@admin_bp.route('/resources')
@admin_required
def resources():
    q = request.args.get('q', '').strip()
    rtype = request.args.get('type', '').strip()
    visibility = request.args.get('visibility', '').strip()

    query = Resource.query
    if q:
        like = f'%{q}%'
        query = (query.join(User, Resource.owner_id == User.id)
                 .filter(or_(Resource.name.ilike(like), Resource.category.ilike(like), User.full_name.ilike(like))))
    if rtype in (TYPE_EQUIPMENT, TYPE_PROFESSIONAL):
        query = query.filter(Resource.resource_type == rtype)
    else:
        rtype = ''
    if visibility == 'hidden':
        query = query.filter(Resource.is_hidden.is_(True))
    elif visibility == 'visible':
        query = query.filter(Resource.is_hidden.is_(False))
    else:
        visibility = ''

    pagination = _paginate(query.order_by(Resource.created_at.desc()))
    return render_template('admin/resources.html', pagination=pagination, resources=pagination.items,
                           q=q, rtype=rtype, visibility=visibility, page_args=_page_args(),
                           type_equipment=TYPE_EQUIPMENT, type_professional=TYPE_PROFESSIONAL)


@admin_bp.route('/resources/<int:resource_id>/<action>', methods=['POST'])
@admin_required
def set_hidden(resource_id, action):
    """Hide a listing from browse / detail (moderation) or show it again. The owner is told."""
    if action not in ('hide', 'unhide'):
        abort(404)
    resource = db.session.get(Resource, resource_id)
    if resource is None:
        abort(404)
    resource.is_hidden = action == 'hide'
    db.session.commit()
    if action == 'hide':
        title, message = 'Listing hidden', f'"{resource.name}" was hidden by the administrator. Contact support if you think this is a mistake.'
    else:
        title, message = 'Listing visible again', f'"{resource.name}" is visible to other users again.'
    create_notification(resource.owner_id, title, message, link=url_for('resource.detail', resource_id=resource.id))
    log_activity('Resource hidden' if action == 'hide' else 'Resource unhidden',
                 f'{resource.name} #{resource.id}', user_id=current_user.id)
    flash(f'"{resource.name}" is now {"hidden" if resource.is_hidden else "visible"}.', 'info')
    return redirect(_next_url(url_for('admin.resources')))


# ---------- bookings ----------

@admin_bp.route('/bookings')
@admin_required
def bookings():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip().lower()

    query = BookingRequest.query
    if q:
        like = f'%{q}%'
        query = query.join(Resource, BookingRequest.resource_id == Resource.id).filter(Resource.name.ilike(like))
    if status in [s.lower() for s in STATUSES]:
        query = query.filter(func.lower(func.trim(BookingRequest.status)) == status)
    else:
        status = ''

    pagination = _paginate(query.order_by(BookingRequest.created_at.desc()))
    return render_template('admin/bookings.html', pagination=pagination, bookings=pagination.items,
                           q=q, status=status, statuses=STATUSES, counts=_booking_counts(), page_args=_page_args())


# ---------- activity logs ----------

@admin_bp.route('/logs')
@admin_required
def logs():
    q = request.args.get('q', '').strip()
    query = ActivityLog.query
    if q:
        like = f'%{q}%'
        query = query.filter(or_(ActivityLog.action.ilike(like), ActivityLog.details.ilike(like)))
    pagination = _paginate(query.order_by(ActivityLog.created_at.desc()), per_page=LOGS_PER_PAGE)
    return render_template('admin/logs.html', pagination=pagination, logs=pagination.items,
                           q=q, page_args=_page_args())
