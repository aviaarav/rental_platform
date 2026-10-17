from app.extensions import db
from app.models.common import utcnow


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking_requests.id'), nullable=False, unique=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False, index=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)   # 1 to 5
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=utcnow)
