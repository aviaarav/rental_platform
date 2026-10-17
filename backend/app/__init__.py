"""Application factory.

Run the dev server from backend/ with:
    flask --app app run --debug
or:
    python run.py
"""
from flask import Flask, flash, redirect, request, url_for
from flask_login import current_user, logout_user

from app.config import FRONTEND_DIR, get_config
from app.extensions import db, login_manager


def create_app(config=None):
    """Build and configure the Flask app.

    `config` is a config class (see app.config) or None to pick one from FLASK_CONFIG.
    """
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / 'templates'),
        static_folder=str(FRONTEND_DIR / 'static'),
    )
    app.config.from_object(config or get_config())

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes import register_blueprints
    register_blueprints(app)

    @app.before_request
    def stop_blocked_users():
        """A blocked user is logged out on the very next request."""
        if request.endpoint == 'static':
            return None
        if current_user.is_authenticated and current_user.is_blocked:
            logout_user()
            flash('Your account has been blocked. Please contact the administrator.', 'danger')
            return redirect(url_for('main.home'))
        return None

    with app.app_context():
        db.create_all()
        seed_admin(app.config['ADMIN_EMAIL'], app.config['ADMIN_PASSWORD'])

    return app


def seed_admin(email, password):
    """Create the default administrator once."""
    from app.models import User

    if User.query.filter_by(email=email).first():
        return
    admin = User(full_name='Administrator', email=email, phone='0000000000',
                 district='Coimbatore', taluk='Coimbatore North', address='Admin Office', role='admin')
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f'Default admin created: {email} / {password}  (change this password later)')
