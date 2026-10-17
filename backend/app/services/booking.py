"""Booking date helpers: validation and overlap checks.

Only start_date and end_date decide availability. service_time is never used.
Blocking statuses: Pending, Approved, Booked, Borrowed.
Rejected, Cancelled and Returned never block a date range.
"""
from datetime import date, datetime

from sqlalchemy import func

from app.constants import BLOCKING_STATUSES
from app.models import BookingRequest


def parse_date(value):
    """Read a date typed as YYYY-MM-DD (the HTML date input format)."""
    try:
        return datetime.strptime((value or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def validate_dates(start_raw, end_raw, allow_past=False):
    """Return (start, end, error). Returns (None, None, None) when both fields are empty."""
    start_raw = (start_raw or '').strip()
    end_raw = (end_raw or '').strip()
    if not start_raw and not end_raw:
        return None, None, None
    start, end = parse_date(start_raw), parse_date(end_raw)
    if start is None or end is None:
        return None, None, 'Select both a valid start date and end date.'
    if end < start:
        return None, None, 'End date cannot be earlier than the start date.'
    if not allow_past and start < date.today():
        return None, None, 'Start date cannot be in the past.'
    return start, end, None


def dates_overlap(start_a, end_a, start_b, end_b):
    """Two date ranges overlap when each one starts before the other one ends (end days included)."""
    return start_a <= end_b and end_a >= start_b


def blocking_bookings(start, end, exclude_booking_id=None):
    """Query of bookings that block the range start..end."""
    query = BookingRequest.query.filter(
        func.lower(func.trim(BookingRequest.status)).in_(BLOCKING_STATUSES),
        BookingRequest.start_date <= end,
        BookingRequest.end_date >= start,
    )
    if exclude_booking_id is not None:
        query = query.filter(BookingRequest.id != exclude_booking_id)
    return query


def has_conflict(resource_id, start, end, exclude_booking_id=None):
    """True when the resource already has a blocking booking inside start..end."""
    return (blocking_bookings(start, end, exclude_booking_id)
            .filter(BookingRequest.resource_id == resource_id).first()) is not None


def booked_resource_ids(start, end):
    """Set of resource ids that are booked for any part of start..end."""
    rows = blocking_bookings(start, end).with_entities(BookingRequest.resource_id).distinct().all()
    return {row[0] for row in rows}


def upcoming_booked_periods(resource_id, limit=5):
    """Next booked date ranges of a resource, as (start, end) pairs. No personal details."""
    rows = (BookingRequest.query
            .filter(BookingRequest.resource_id == resource_id,
                    func.lower(func.trim(BookingRequest.status)).in_(BLOCKING_STATUSES),
                    BookingRequest.end_date >= date.today())
            .order_by(BookingRequest.start_date).limit(limit).all())
    return [(row.start_date, row.end_date) for row in rows]