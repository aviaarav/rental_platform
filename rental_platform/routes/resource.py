from math import ceil

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from data.categories import (AVAILABILITY_OPTIONS, CHARGE_TYPES, CONDITIONS,
                             EQUIPMENT_CATEGORIES, PICKUP_METHODS, SERVICE_CATEGORIES)
from data.tn_locations import DISTRICTS, is_valid_location
from extensions import db
from models import TYPE_EQUIPMENT, TYPE_PROFESSIONAL, Resource
from utils.booking import booked_resource_ids, has_conflict, upcoming_booked_periods, validate_dates
from utils.geo import haversine_km, is_valid_pair, parse_coordinate, route_points
from utils.notify import log_activity
from utils.uploads import delete_image, folder_for, save_image

resource_bp = Blueprint('resource', __name__, url_prefix='/resources')


def _form_options():
    """Lists used by the dropdowns in the add / edit forms."""
    return dict(districts=DISTRICTS, equipment_categories=EQUIPMENT_CATEGORIES,
                service_categories=SERVICE_CATEGORIES, conditions=CONDITIONS,
                pickup_methods=PICKUP_METHODS, charge_types=CHARGE_TYPES,
                availability_options=AVAILABILITY_OPTIONS)


def _validate(form, kind):
    """Validate the form. Returns (clean_data, error_list)."""
    errors = []
    data = {
        'name': form.get('name', '').strip(),
        'category': form.get('category', '').strip(),
        'description': form.get('description', '').strip(),
        'district': form.get('district', '').strip(),
        'taluk': form.get('taluk', '').strip(),
        'availability': form.get('availability', '').strip(),
    }
    categories = EQUIPMENT_CATEGORIES if kind == TYPE_EQUIPMENT else SERVICE_CATEGORIES

    if not 3 <= len(data['name']) <= 120:
        errors.append('Name must be 3 to 120 characters.')
    if data['category'] not in categories:
        errors.append('Select a valid category.')
    if not 10 <= len(data['description']) <= 1000:
        errors.append('Description must be 10 to 1000 characters.')
    if not is_valid_location(data['district'], data['taluk']):
        errors.append('Select a valid district and taluk.')
    if data['availability'] not in AVAILABILITY_OPTIONS:
        errors.append('Select a valid availability.')

    price = parse_coordinate(form.get('price'))
    if price is None or price <= 0 or price > 10000000:
        errors.append('Enter a valid amount greater than zero.')
    else:
        data['price'] = price

    # latitude and longitude are optional, but must be valid together
    lat_raw = form.get('latitude', '').strip()
    lng_raw = form.get('longitude', '').strip()
    if lat_raw or lng_raw:
        if is_valid_pair(lat_raw, lng_raw):
            data['latitude'] = float(lat_raw)
            data['longitude'] = float(lng_raw)
        else:
            errors.append('Enter a valid latitude (-90 to 90) and longitude (-180 to 180), or leave both empty.')
    else:
        data['latitude'] = None
        data['longitude'] = None

    if kind == TYPE_EQUIPMENT:
        data['condition'] = form.get('condition', '').strip()
        data['pickup_method'] = form.get('pickup_method', '').strip()
        data['charge_type'] = 'Per Day'
        if data['condition'] not in CONDITIONS:
            errors.append('Select the equipment condition.')
        if data['pickup_method'] not in PICKUP_METHODS:
            errors.append('Select a pickup method.')
        deposit_raw = form.get('security_deposit', '').strip()
        if deposit_raw == '':
            data['security_deposit'] = 0
        else:
            deposit = parse_coordinate(deposit_raw)
            if deposit is None or deposit < 0 or deposit > 10000000:
                errors.append('Security deposit must be zero or more.')
            else:
                data['security_deposit'] = deposit
    else:
        data['charge_type'] = form.get('charge_type', '').strip()
        if data['charge_type'] not in CHARGE_TYPES:
            errors.append('Select the charge type.')
        experience = parse_coordinate(form.get('experience'))
        if experience is None or not 0 <= experience <= 60 or experience != int(experience):
            errors.append('Experience must be a whole number of years (0 to 60).')
        else:
            data['experience'] = int(experience)

    return data, errors


def _form_from(resource):
    """Turn a saved resource into the plain dict the form templates read."""
    def text(value):
        return '' if value is None else str(value)
    return {
        'name': resource.name, 'category': resource.category, 'description': resource.description,
        'district': resource.district, 'taluk': resource.taluk, 'availability': resource.availability,
        'price': f'{resource.price:g}', 'charge_type': resource.charge_type,
        'condition': text(resource.condition), 'pickup_method': text(resource.pickup_method),
        'security_deposit': f'{(resource.security_deposit or 0):g}',
        'experience': text(resource.experience),
        'latitude': text(resource.latitude), 'longitude': text(resource.longitude),
    }


def _owned_resource(resource_id):
    """Load a resource that belongs to the logged-in user, or stop with 404 / 403."""
    resource = db.session.get(Resource, resource_id)
    if resource is None:
        abort(404)
    if resource.owner_id != current_user.id:
        abort(403)
    return resource


def _add(kind, template):
    if request.method == 'POST':
        data, errors = _validate(request.form, kind)
        image_name = None
        if not errors:
            try:
                image_name = save_image(request.files.get('image'), folder_for(kind))
            except ValueError as error:
                errors.append(str(error))
        if errors:
            for message in errors:
                flash(message, 'danger')
            return render_template(template, form=request.form, **_form_options())

        resource = Resource(owner_id=current_user.id, resource_type=kind, image=image_name, **data)
        db.session.add(resource)
        db.session.commit()
        log_activity('Resource created', f'{kind}: {resource.name}', user_id=current_user.id)
        flash('Your listing has been added.', 'success')
        return redirect(url_for('resource.my_items'))

    return render_template(template, form={}, **_form_options())


@resource_bp.route('/add-equipment', methods=['GET', 'POST'])
@login_required
def add_equipment():
    return _add(TYPE_EQUIPMENT, 'resources/add_equipment.html')


@resource_bp.route('/add-service', methods=['GET', 'POST'])
@login_required
def add_service():
    return _add(TYPE_PROFESSIONAL, 'resources/add_service.html')


@resource_bp.route('/my-items')
@login_required
def my_items():
    items = (Resource.query.filter_by(owner_id=current_user.id)
             .order_by(Resource.created_at.desc()).all())
    return render_template('resources/my_items.html', items=items)


PER_PAGE = 9
RADIUS_OPTIONS = (5, 10, 25, 50, 100)


def _location_from_args(args):
    """The user's current location from ?lat=&lng= (None, None when missing or invalid)."""
    lat_raw, lng_raw = args.get('lat', ''), args.get('lng', '')
    if is_valid_pair(lat_raw, lng_raw):
        return float(lat_raw), float(lng_raw)
    return None, None


@resource_bp.route('/browse')
@login_required
def browse():
    args = request.args
    keyword = args.get('q', '').strip()
    rtype = args.get('type', '').strip()
    category = args.get('category', '').strip()
    district = args.get('district', '').strip()
    show_booked = args.get('show_booked') == '1'
    user_lat, user_lng = _location_from_args(args)
    location_on = user_lat is not None

    radius = args.get('radius', '').strip()
    radius = int(radius) if radius.isdigit() and int(radius) in RADIUS_OPTIONS else None
    if radius and not location_on:
        flash('Turn on "Use My Current Location" to filter by distance.', 'info')
        radius = None

    start, end, date_error = validate_dates(args.get('start'), args.get('end'))
    if date_error:
        flash(date_error, 'warning')

    # General listing visibility: every visible listing of other users, even without any date filter.
    query = Resource.query.filter(Resource.owner_id != current_user.id, Resource.is_hidden.is_(False))
    if rtype in (TYPE_EQUIPMENT, TYPE_PROFESSIONAL):
        query = query.filter(Resource.resource_type == rtype)
    if category:
        query = query.filter(Resource.category == category)
    if district:
        query = query.filter(Resource.district == district)
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(or_(Resource.name.ilike(like), Resource.category.ilike(like),
                                 Resource.description.ilike(like)))

    # Availability for a date range is a separate question: decided only by blocking bookings.
    booked_ids = booked_resource_ids(start, end) if start and end else set()

    entries, hidden_booked = [], 0
    for resource in query.all():
        distance = resource.distance_from(user_lat, user_lng) if location_on else None
        if radius and (distance is None or distance > radius):
            continue
        booked = resource.id in booked_ids
        if booked and not show_booked:
            hidden_booked += 1
            continue
        entries.append({'r': resource, 'distance': distance, 'booked': booked})

    def sort_key(entry):
        not_open = entry['booked'] or entry['r'].availability != 'Available'
        distance = entry['distance']
        return (1 if not_open else 0, distance is None, distance or 0, -entry['r'].id)

    entries.sort(key=sort_key)

    total = len(entries)
    pages = max(1, ceil(total / PER_PAGE))
    page = args.get('page', '1')
    page = min(max(int(page), 1), pages) if page.isdigit() else 1
    page_entries = entries[(page - 1) * PER_PAGE: page * PER_PAGE]
    for entry in page_entries:
        entry['rating'] = entry['r'].average_rating
        entry['reviews'] = entry['r'].review_count

    link_args = {}                       # carried to the detail page
    if location_on:
        link_args.update(lat=user_lat, lng=user_lng)
    if start and end:
        link_args.update(start=start.isoformat(), end=end.isoformat())

    return render_template(
        'resources/browse.html', entries=page_entries, total=total, page=page, pages=pages,
        page_args={k: v for k, v in args.items() if v and k != 'page'}, link_args=link_args,
        keyword=keyword, rtype=rtype, category=category, district=district, radius=radius,
        show_booked=show_booked, hidden_booked=hidden_booked, location_on=location_on,
        user_lat=user_lat, user_lng=user_lng, date_filter=bool(start and end), start=start, end=end,
        radius_options=RADIUS_OPTIONS, districts=DISTRICTS,
        equipment_categories=EQUIPMENT_CATEGORIES, service_categories=SERVICE_CATEGORIES)


@resource_bp.route('/<int:resource_id>')
@login_required
def detail(resource_id):
    resource = db.session.get(Resource, resource_id)
    if resource is None:
        abort(404)
    if resource.is_hidden and resource.owner_id != current_user.id and not current_user.is_admin:
        abort(404)

    is_owner = resource.owner_id == current_user.id
    user_lat, user_lng = _location_from_args(request.args)
    distance, points = None, None
    if user_lat is not None and resource.has_coordinates and not is_owner:
        distance = haversine_km(user_lat, user_lng, resource.latitude, resource.longitude)
        points = route_points(user_lat, user_lng, resource.latitude, resource.longitude)

    start, end, date_error = validate_dates(request.args.get('start'), request.args.get('end'))
    if date_error:
        flash(date_error, 'warning')
    availability = None
    if start and end:
        free = resource.availability == 'Available' and not has_conflict(resource.id, start, end)
        availability = {'start': start, 'end': end, 'free': free}

    return render_template('resources/detail.html', resource=resource, is_owner=is_owner,
                           user_lat=user_lat, user_lng=user_lng, distance=distance, points=points,
                           availability=availability, start=start, end=end,
                           booked_periods=upcoming_booked_periods(resource.id))


@resource_bp.route('/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(resource_id):
    resource = _owned_resource(resource_id)

    if request.method == 'POST':
        data, errors = _validate(request.form, resource.resource_type)
        new_image = None
        if not errors:
            try:
                new_image = save_image(request.files.get('image'), folder_for(resource.resource_type))
            except ValueError as error:
                errors.append(str(error))
        if errors:
            for message in errors:
                flash(message, 'danger')
            return render_template('resources/edit.html', resource=resource,
                                   form=request.form, **_form_options())

        for field, value in data.items():
            setattr(resource, field, value)
        if new_image:
            delete_image(folder_for(resource.resource_type), resource.image)
            resource.image = new_image
        db.session.commit()
        log_activity('Resource updated', f'{resource.resource_type}: {resource.name}', user_id=current_user.id)
        flash('Listing updated.', 'success')
        return redirect(url_for('resource.detail', resource_id=resource.id))

    return render_template('resources/edit.html', resource=resource,
                           form=_form_from(resource), **_form_options())


@resource_bp.route('/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete(resource_id):
    resource = _owned_resource(resource_id)
    if resource.bookings.count() > 0:
        flash('This listing has booking history, so it cannot be deleted. '
              'Edit it and set Availability to Unavailable instead.', 'warning')
        return redirect(url_for('resource.my_items'))

    name = resource.name
    delete_image(folder_for(resource.resource_type), resource.image)
    db.session.delete(resource)
    db.session.commit()
    log_activity('Resource deleted', name, user_id=current_user.id)
    flash('Listing deleted.', 'success')
    return redirect(url_for('resource.my_items'))