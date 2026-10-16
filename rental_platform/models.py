from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager
from utils.geo import haversine_km, is_valid_pair

# ---------- constants ----------
ROLE_USER = 'user'
ROLE_ADMIN = 'admin'

TYPE_EQUIPMENT = 'Equipment'
TYPE_PROFESSIONAL = 'Professional'

STATUS_PENDING = 'Pending'
STATUS_APPROVED = 'Approved'
STATUS_REJECTED = 'Rejected'
STATUS_CANCELLED = 'Cancelled'
STATUS_BORROWED = 'Borrowed'
STATUS_RETURNED = 'Returned'

# Statuses that block the dates of a resource (compare in lower case).
BLOCKING_STATUSES = ('pending', 'approved', 'booked', 'borrowed')


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------- User ----------
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


# ---------- Resource (equipment + professional service) ----------
class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    resource_type = db.Column(db.String(15), nullable=False, default=TYPE_EQUIPMENT)  # Equipment / Professional
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))                      # file name inside static/uploads/...
    # equipment only
    condition = db.Column(db.String(10))                   # New / Good / Average
    pickup_method = db.Column(db.String(30))               # Owner's Home / Mutual Location / Delivery
    security_deposit = db.Column(db.Float, default=0)
    # professional only
    experience = db.Column(db.Integer)                     # years
    # common
    price = db.Column(db.Float, nullable=False, default=0)  # rental amount or service charge
    charge_type = db.Column(db.String(10), nullable=False, default='Per Day')  # Per Day / Per Hour
    district = db.Column(db.String(60), nullable=False)
    taluk = db.Column(db.String(60), nullable=False)
    availability = db.Column(db.String(15), nullable=False, default='Available')  # Available / Unavailable
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)  # admin moderation
    created_at = db.Column(db.DateTime, default=utcnow)

    # No delete cascade: booking and review history must never be removed by accident.
    bookings = db.relationship('BookingRequest', backref='resource', lazy='dynamic')
    reviews = db.relationship('Review', backref='resource', lazy='dynamic')

    @property
    def is_equipment(self):
        return self.resource_type == TYPE_EQUIPMENT

    @property
    def is_professional(self):
        return self.resource_type == TYPE_PROFESSIONAL

    @property
    def has_coordinates(self):
        return is_valid_pair(self.latitude, self.longitude)

    @property
    def price_label(self):
        unit = 'hour' if self.charge_type == 'Per Hour' else 'day'
        return f'Rs. {self.price:,.0f} / {unit}'
    
    @property
    def image_path(self):
        """Path inside static/ for the uploaded image, or None."""
        if not self.image:
            return None
        folder = 'equipment' if self.is_equipment else 'professional'
        return f'uploads/{folder}/{self.image}'

    @property
    def average_rating(self):
        avg = db.session.query(db.func.avg(Review.rating)).filter(Review.resource_id == self.id).scalar()
        return round(float(avg), 1) if avg is not None else None

    @property
    def review_count(self):
        return self.reviews.count()

    def distance_from(self, lat, lng):
        """Km from a point to this resource, or None when coordinates are missing / invalid."""
        if not self.has_coordinates:
            return None
        return haversine_km(lat, lng, self.latitude, self.longitude)

    def __repr__(self):
        return f'<Resource {self.id} {self.name}>'


# ---------- BookingRequest ----------
class BookingRequest(db.Model):
    __tablename__ = 'booking_requests'

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False, index=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # dates decide availability; service_time is NEVER used for conflict checks
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    service_time = db.Column(db.String(20))        # pickup time (equipment) / start time (professional)
    return_time = db.Column(db.String(20))         # equipment only
    duration_hours = db.Column(db.Integer)         # professional only

    purpose = db.Column(db.String(120))
    purpose_details = db.Column(db.String(255))
    pickup_method = db.Column(db.String(30))       # equipment pickup method / professional service mode
    urgency = db.Column(db.String(15))             # professional only
    address = db.Column(db.String(255))            # meeting / delivery / service address
    request_district = db.Column(db.String(60))
    request_taluk = db.Column(db.String(60))

    borrower_latitude = db.Column(db.Float)
    borrower_longitude = db.Column(db.Float)

    status = db.Column(db.String(15), nullable=False, default=STATUS_PENDING)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    review = db.relationship('Review', backref='booking', uselist=False)

    @property
    def status_key(self):
        return (self.status or '').strip().lower()

    @property
    def is_blocking(self):
        return self.status_key in BLOCKING_STATUSES

    @property
    def has_borrower_location(self):
        return is_valid_pair(self.borrower_latitude, self.borrower_longitude)

    @property
    def distance_km(self):
        """Borrower to resource distance, only when both coordinate pairs are valid."""
        if not (self.has_borrower_location and self.resource and self.resource.has_coordinates):
            return None
        return haversine_km(self.borrower_latitude, self.borrower_longitude,
                            self.resource.latitude, self.resource.longitude)

    def __repr__(self):
        return f'<BookingRequest {self.id} {self.status}>'


# ---------- Review ----------
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking_requests.id'), nullable=False, unique=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False, index=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)   # 1 to 5
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=utcnow)


# ---------- Notification ----------
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)


# ---------- ActivityLog ----------
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))   # None for system events
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utcnow)