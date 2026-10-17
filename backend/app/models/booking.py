from app.constants import BLOCKING_STATUSES, STATUS_PENDING
from app.extensions import db
from app.models.common import utcnow
from app.utils.geo import haversine_km, is_valid_pair


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
