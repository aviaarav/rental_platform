"""Reviews: a borrower rates a resource once, after the booking is returned / completed."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.constants import STATUS_RETURNED
from app.extensions import db
from app.models import BookingRequest, Review
from app.services.notify import create_notification, log_activity

review_bp = Blueprint('review', __name__, url_prefix='/reviews')


@review_bp.route('/add/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def add(booking_id):
    booking = db.session.get(BookingRequest, booking_id)
    if booking is None:
        abort(404)
    if booking.borrower_id != current_user.id:
        abort(403)
    if booking.status_key != STATUS_RETURNED.lower():
        flash('You can write a review only after the booking is marked as returned / completed.', 'warning')
        return redirect(url_for('request.sent'))
    if booking.review is not None:
        flash('You have already reviewed this booking.', 'info')
        return redirect(url_for('resource.detail', resource_id=booking.resource_id))

    if request.method == 'POST':
        rating_raw = request.form.get('rating', '').strip()
        comment = request.form.get('comment', '').strip()
        errors = []
        if not rating_raw.isdigit() or not 1 <= int(rating_raw) <= 5:
            errors.append('Choose a rating from 1 to 5 stars.')
        if len(comment) > 500:
            errors.append('Keep the comment under 500 characters.')
        if errors:
            for message in errors:
                flash(message, 'danger')
            return render_template('reviews/add.html', booking=booking, form=request.form)

        review = Review(booking_id=booking.id, resource_id=booking.resource_id,
                        reviewer_id=current_user.id, rating=int(rating_raw), comment=comment or None)
        db.session.add(review)
        db.session.commit()
        create_notification(booking.owner_id, 'New review',
                            f'{current_user.full_name} rated "{booking.resource.name}" {review.rating}/5.',
                            link=url_for('resource.detail', resource_id=booking.resource_id))
        log_activity('Review added', f'{booking.resource.name} {review.rating}/5', user_id=current_user.id)
        flash('Thank you for your review.', 'success')
        return redirect(url_for('resource.detail', resource_id=booking.resource_id))

    return render_template('reviews/add.html', booking=booking, form={})
