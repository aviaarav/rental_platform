from app.constants import TYPE_EQUIPMENT, TYPE_PROFESSIONAL
from app.extensions import db
from app.models.common import utcnow
from app.models.review import Review
from app.utils.geo import haversine_km, is_valid_pair


class Resource(db.Model):
    """A piece of equipment for rent or a professional service for hire."""

    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    resource_type = db.Column(db.String(15), nullable=False, default=TYPE_EQUIPMENT)  # Equipment / Professional
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))                      # file name inside UPLOAD_FOLDER/<equipment|professional>/
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
        """Path of the uploaded image relative to UPLOAD_FOLDER, or None.

        Serve it with url_for('uploads.serve', filename=resource.image_path).
        """
        if not self.image:
            return None
        folder = 'equipment' if self.is_equipment else 'professional'
        return f'{folder}/{self.image}'

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
