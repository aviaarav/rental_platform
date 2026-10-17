import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.data.tn_locations import DISTRICTS, is_valid_location
from app.extensions import db
from app.constants import ROLE_USER
from app.models import User
from app.services.notify import log_activity

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _home_for(user):
    return url_for('admin.dashboard') if user.is_admin else url_for('dashboard.index')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))

    if request.method == 'POST':
        f = request.form
        full_name = f.get('full_name', '').strip()
        email = f.get('email', '').strip().lower()
        phone = re.sub(r'\s+', '', f.get('phone', ''))
        password = f.get('password', '')
        confirm = f.get('confirm_password', '')
        district = f.get('district', '').strip()
        taluk = f.get('taluk', '').strip()
        address = f.get('address', '').strip()

        errors = []
        if len(full_name) < 3:
            errors.append('Full name must be at least 3 characters.')
        if not EMAIL_RE.match(email):
            errors.append('Enter a valid email address.')
        elif User.query.filter_by(email=email).first():
            errors.append('This email is already registered.')
        if not re.fullmatch(r'\d{10}', phone):
            errors.append('Phone number must be 10 digits.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Password and confirm password do not match.')
        if not is_valid_location(district, taluk):
            errors.append('Select a valid district and taluk.')
        if len(address) < 5:
            errors.append('Enter your address.')

        if errors:
            for message in errors:
                flash(message, 'danger')
            return render_template('auth/register.html', districts=DISTRICTS, form=f)

        user = User(full_name=full_name, email=email, phone=phone,
                    district=district, taluk=taluk, address=address, role=ROLE_USER)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        log_activity('User registered', f'{full_name} ({email})', user_id=user.id)
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', districts=DISTRICTS, form={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, role=ROLE_USER).first()

        if user is None or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
        elif user.is_blocked:
            flash('Your account has been blocked. Please contact the administrator.', 'danger')
        else:
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')


@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, role='admin').first()

        if user is None or not user.check_password(password):
            flash('Invalid administrator email or password.', 'danger')
        else:
            login_user(user)
            return redirect(url_for('admin.dashboard'))

    return render_template('auth/admin_login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))