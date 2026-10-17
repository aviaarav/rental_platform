"""The logged-in user's own profile: view, edit details, change password."""
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.data.tn_locations import DISTRICTS, is_valid_location
from app.extensions import db
from app.services.notify import log_activity

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


def _form_from(user):
    return {'full_name': user.full_name, 'phone': user.phone, 'district': user.district,
            'taluk': user.taluk, 'address': user.address}


def _stats(user):
    return {'resources': user.resources.count(), 'received': user.bookings_received.count(),
            'sent': user.bookings_made.count(), 'reviews': user.reviews_written.count()}


@profile_bp.route('', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        f = request.form
        full_name = f.get('full_name', '').strip()
        phone = re.sub(r'\s+', '', f.get('phone', ''))
        district = f.get('district', '').strip()
        taluk = f.get('taluk', '').strip()
        address = f.get('address', '').strip()

        errors = []
        if len(full_name) < 3:
            errors.append('Full name must be at least 3 characters.')
        if not re.fullmatch(r'\d{10}', phone):
            errors.append('Phone number must be 10 digits.')
        if not is_valid_location(district, taluk):
            errors.append('Select a valid district and taluk.')
        if len(address) < 5:
            errors.append('Enter your address.')
        if errors:
            for message in errors:
                flash(message, 'danger')
            return render_template('profile.html', districts=DISTRICTS, form=f, stats=_stats(current_user),
                                   editing=True)

        current_user.full_name = full_name
        current_user.phone = phone
        current_user.district = district
        current_user.taluk = taluk
        current_user.address = address
        db.session.commit()
        log_activity('Profile updated', current_user.email, user_id=current_user.id)
        flash('Profile updated.', 'success')
        return redirect(url_for('profile.index'))

    return render_template('profile.html', districts=DISTRICTS, form=_form_from(current_user),
                           stats=_stats(current_user), editing=request.args.get('edit') == '1')


@profile_bp.route('/password', methods=['POST'])
@login_required
def change_password():
    current = request.form.get('current_password', '')
    new = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')

    errors = []
    if not current_user.check_password(current):
        errors.append('Current password is incorrect.')
    if len(new) < 6:
        errors.append('New password must be at least 6 characters.')
    if new != confirm:
        errors.append('New password and confirm password do not match.')
    if errors:
        for message in errors:
            flash(message, 'danger')
        return redirect(url_for('profile.index'))

    current_user.set_password(new)
    db.session.commit()
    log_activity('Password changed', current_user.email, user_id=current_user.id)
    flash('Password changed.', 'success')
    return redirect(url_for('profile.index'))
