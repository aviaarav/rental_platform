"""Booking requests: create one, list sent / received ones, and move them through their statuses."""
import re

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.constants import (
    STATUS_APPROVED,
    STATUS_BORROWED,
    STATUS_CANCELLED,
    STATUS_PENDING,
    STATUS_REJECTED,
    STATUS_RETURNED,
)
from app.data.categories import EQUIPMENT_PURPOSES, PICKUP_METHODS, SERVICE_MODES, SERVICE_PURPOSES, URGENCY_OPTIONS
from app.data.tn_locations import DISTRICTS, is_valid_location
from app.extensions import db
from app.models import BookingRequest, Resource
from app.services.booking import has_conflict, validate_dates
from app.services.notify import create_notification, log_activity
from app.utils.geo import is_valid_pair, route_points

request_bp = Blueprint('request', __name__, url_prefix='/requests')

TIME_RE = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')
STATUS_FILTERS = [STATUS_PENDING, STATUS_APPROVED, STATUS_BORROWED, STATUS_RETURNED,
                  STATUS_REJECTED, STATUS_CANCELLED]

# action -> (who may do it, statuses it applies to, resulting status, past-tense label)
TRANSITIONS = {
    'approve':  ('owner',    (STATUS_PENDING,),                 STATUS_APPROVED,  'approved'),
    'reject':   ('owner',    (STATUS_PENDING,),                 STATUS_REJECTED,  'rejected'),
    'borrowed': ('owner',    (STATUS_APPROVED,),                STATUS_BORROWED,  'marked as borrowed / started'),
    'returned': ('owner',    (STATUS_BORROWED,),                STATUS_RETURNED,  'marked as returned / completed'),
    'cancel':   ('borrower', (STATUS_PENDING, STATUS_APPROVED), STATUS_CANCELLED, 'cancelled'),
}


def _form_options():
    return {'districts': DISTRICTS, 'pickup_methods': PICKUP_METHODS, 'service_modes': SERVICE_MODES,
            'urgency_options': URGENCY_OPTIONS, 'equipment_purposes': EQUIPMENT_PURPOSES,
            'service_purposes': SERVICE_PURPOSES}


def _dates(booking):
    return f'{booking.start_date:%d %b} - {booking.end_date:%d %b %Y}'


def _validate(form, resource):
    """Validate a booking form for `resource`. Returns (clean_data, error_list)."""
    errors = []
    data = {
        'purpose': form.get('purpose', '').strip(),
        'purpose_details': form.get('purpose_details', '').strip()[:255] or None,
        'address': form.get('address', '').strip(),
        'request_district': form.get('request_district', '').strip(),
        'request_taluk': form.get('request_taluk', '').strip(),
        'service_time': form.get('service_time', '').strip(),
        'pickup_method': form.get('pickup_method', '').strip(),
    }

    start, end, date_error = validate_dates(form.get('start_date'), form.get('end_date'))
    if date_error:
        errors.append(date_error)
    elif start is None:
        errors.append('Select a start date and an end date.')
    else:
        data['start_date'], data['end_date'] = start, end
        if has_conflict(resource.id, start, end):
            errors.append('This listing is already booked for part of those dates. Choose different dates.')

    if not 3 <= len(data['purpose']) <= 120:
        errors.append('Describe the purpose in 3 to 120 characters.')
    if not 5 <= len(data['address']) <= 255:
        errors.append('Enter the meeting, delivery or service address.')
    if not is_valid_location(data['request_district'], data['request_taluk']):
        errors.append('Select a valid district and taluk.')
    if not TIME_RE.match(data['service_time']):
        errors.append('Enter a valid time (HH:MM).')

    lat_raw = form.get('borrower_latitude', '').strip()
    lng_raw = form.get('borrower_longitude', '').strip()
    if lat_raw or lng_raw:
        if is_valid_pair(lat_raw, lng_raw):
            data['borrower_latitude'], data['borrower_longitude'] = float(lat_raw), float(lng_raw)
        else:
            errors.append('Enter a valid latitude and longitude, or leave both empty.')

    if resource.is_equipment:
        data['return_time'] = form.get('return_time', '').strip()
        if not TIME_RE.match(data['return_time']):
            errors.append('Enter a valid return time (HH:MM).')
        if data['pickup_method'] not in PICKUP_METHODS:
            errors.append('Select a pickup method.')
    else:
        data['urgency'] = form.get('urgency', '').strip()
        if data['urgency'] not in URGENCY_OPTIONS:
            errors.append('Select the urgency.')
        if data['pickup_method'] not in SERVICE_MODES:
            errors.append('Select how the service should be provided.')
        hours_raw = form.get('duration_hours', '').strip()
        if not hours_raw.isdigit() or not 1 <= int(hours_raw) <= 24:
            errors.append('Duration must be 1 to 24 hours per day.')
        else:
            data['duration_hours'] = int(hours_raw)

    return data, errors


@request_bp.route('/new/<int:resource_id>', methods=['GET', 'POST'])
@login_required
def new(resource_id):
    resource = db.session.get(Resource, resource_id)
    if resource is None or resource.is_hidden:
        abort(404)
    if resource.owner_id == current_user.id:
        flash('You cannot book your own listing.', 'warning')
        return redirect(url_for('resource.detail', resource_id=resource.id))
    if resource.availability != 'Available':
        flash('This listing is currently unavailable for booking.', 'warning')
        return redirect(url_for('resource.detail', resource_id=resource.id))

    template = 'requests/new_equipment.html' if resource.is_equipment else 'requests/new_service.html'

    if request.method == 'POST':
        data, errors = _validate(request.form, resource)
        if errors:
            for message in errors:
                flash(message, 'danger')
            return render_template(template, resource=resource, form=request.form, dates_free=None,
                                   **_form_options())

        booking = BookingRequest(resource_id=resource.id, borrower_id=current_user.id,
                                 owner_id=resource.owner_id, status=STATUS_PENDING, **data)
        db.session.add(booking)
        db.session.commit()
        create_notification(resource.owner_id, 'New booking request',
                            f'{current_user.full_name} requested "{resource.name}" for {_dates(booking)}.',
                            link=url_for('request.received', resource_id=resource.id))
        log_activity('Booking requested', f'{resource.name} #{booking.id}', user_id=current_user.id)
        flash('Your request has been sent to the owner.', 'success')
        return redirect(url_for('request.sent'))

    # Prefill from the availability check on the detail page and from the user's own profile.
    form = {
        'start_date': request.args.get('start', ''), 'end_date': request.args.get('end', ''),
        'request_district': current_user.district, 'request_taluk': current_user.taluk,
        'address': current_user.address,
        'borrower_latitude': request.args.get('lat', ''), 'borrower_longitude': request.args.get('lng', ''),
    }
    # When the dates came from the detail / browse page, say up front whether they are free.
    start, end, _ = validate_dates(form['start_date'], form['end_date'])
    dates_free = (not has_conflict(resource.id, start, end)) if start and end else None
    return render_template(template, resource=resource, form=form, dates_free=dates_free, **_form_options())


@request_bp.route('/sent')
@login_required
def sent():
    bookings = current_user.bookings_made.order_by(BookingRequest.created_at.desc()).all()
    return render_template('requests/sent.html', bookings=bookings)


@request_bp.route('/received')
@login_required
def received():
    query = current_user.bookings_received

    resource = None
    resource_id = request.args.get('resource_id', '')
    if resource_id.isdigit():
        resource = db.session.get(Resource, int(resource_id))
        if resource is not None and resource.owner_id == current_user.id:
            query = query.filter(BookingRequest.resource_id == resource.id)
        else:
            resource = None

    status = request.args.get('status', '').strip().lower()
    if status in [s.lower() for s in STATUS_FILTERS]:
        query = query.filter(func.lower(func.trim(BookingRequest.status)) == status)
    else:
        status = ''

    bookings = query.order_by(BookingRequest.created_at.desc()).all()
    rows = []
    for booking in bookings:
        points = None
        if booking.distance_km is not None:
            points = route_points(booking.borrower_latitude, booking.borrower_longitude,
                                  booking.resource.latitude, booking.resource.longitude)
        rows.append({'b': booking, 'points': points})
    return render_template('requests/received.html', rows=rows, resource=resource,
                           status=status, status_filters=STATUS_FILTERS)


@request_bp.route('/<int:booking_id>/<action>', methods=['POST'])
@login_required
def update(booking_id, action):
    """Move a booking to its next status. Owners approve / reject / hand over / take back; borrowers cancel."""
    transition = TRANSITIONS.get(action)
    if transition is None:
        abort(404)
    role, allowed_from, new_status, label = transition

    booking = db.session.get(BookingRequest, booking_id)
    if booking is None:
        abort(404)
    actor_id = booking.owner_id if role == 'owner' else booking.borrower_id
    if actor_id != current_user.id:
        abort(403)

    back = url_for('request.received') if role == 'owner' else url_for('request.sent')
    if booking.status_key not in [s.lower() for s in allowed_from]:
        flash(f'This request is {booking.status} and cannot be {label}.', 'warning')
        return redirect(back)

    booking.status = new_status
    db.session.commit()

    other_id = booking.borrower_id if role == 'owner' else booking.owner_id
    if new_status == STATUS_RETURNED:
        link = url_for('review.add', booking_id=booking.id)
    elif role == 'owner':
        link = url_for('request.sent')
    else:
        link = url_for('request.received')
    create_notification(other_id, f'Request {new_status.lower()}',
                        f'"{booking.resource.name}" ({_dates(booking)}) was {label} by {current_user.full_name}.',
                        link=link)
    log_activity(f'Booking {new_status.lower()}', f'{booking.resource.name} #{booking.id}', user_id=current_user.id)
    flash(f'Request {label}.', 'success')
    return redirect(back)
