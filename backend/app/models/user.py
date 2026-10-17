from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.constants import ROLE_ADMIN, ROLE_USER
from app.extensions import db, login_manager
from app.models.common import utcnow


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(60), nullable=False)
    taluk = db.Column(db.String(60), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default=ROLE_USER)
    is_blocked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    resources = db.relationship('Resource', backref='owner', lazy='dynamic',
                                foreign_keys='Resource.owner_id')
    bookings_made = db.relationship('BookingRequest', backref='borrower', lazy='dynamic',
                                    foreign_keys='BookingRequest.borrower_id')
    bookings_received = db.relationship('BookingRequest', backref='owner', lazy='dynamic',
                                        foreign_keys='BookingRequest.owner_id')
    reviews_written = db.relationship('Review', backref='reviewer', lazy='dynamic',
                                      foreign_keys='Review.reviewer_id')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    activities = db.relationship('ActivityLog', backref='actor', lazy='dynamic')

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
