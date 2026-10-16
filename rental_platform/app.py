import os

from flask import Flask, flash, redirect, request, url_for
from flask_login import current_user, logout_user

from extensions import db, login_manager
from models import User
from routes import register_blueprints

ADMIN_EMAIL = 'admin@rentserve.in'
ADMIN_PASSWORD = 'Admin@123'


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key-before-deployment')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rental.db'   # saved in the instance/ folder
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024               # 5 MB uploads
    app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}

    db.init_app(app)
    login_manager.init_app(app)
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
        seed_admin()

    return app


def seed_admin():
    """Create the default administrator once."""
    if User.query.filter_by(email=ADMIN_EMAIL).first():
        return
    admin = User(full_name='Administrator', email=ADMIN_EMAIL, phone='0000000000',
                 district='Coimbatore', taluk='Coimbatore North', address='Admin Office', role='admin')
    admin.set_password(ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.commit()
    print(f'Default admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}  (change this password later)')


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)