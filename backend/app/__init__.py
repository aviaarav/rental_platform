"""Application factory.

Run the dev server from backend/ with:
    flask --app app run --debug
or:
    python run.py

First-time setup (also from backend/):
    flask --app app db upgrade      # create / migrate the database
    flask --app app seed-admin      # create the default administrator
"""
from flask import Flask, flash, redirect, request, url_for
from flask_login import current_user, logout_user

from app.config import FRONTEND_DIR, get_config
from app.extensions import db, login_manager, migrate


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
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importing the package registers every table with SQLAlchemy (needed by
    # Flask-Migrate) and the Flask-Login user loader.
    from app import models  # noqa: F401

    from app.routes import register_blueprints
    register_blueprints(app)

    from app.cli import register_commands
    register_commands(app)

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

    return app
