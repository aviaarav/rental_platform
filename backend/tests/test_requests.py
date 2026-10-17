from app.constants import STATUS_APPROVED, STATUS_BORROWED, STATUS_CANCELLED, STATUS_PENDING, STATUS_RETURNED
from app.models import BookingRequest, Notification
from tests.conftest import equipment_request_form, login, logout, make_user, service_request_form


def _send(client, resource, form):
    return client.post(f'/requests/new/{resource.id}', data=form)


def test_request_form_pages_render(client, borrower, equipment, service):
    login(client, borrower.email)
    assert client.get(f'/requests/new/{equipment.id}').status_code == 200
    assert client.get(f'/requests/new/{service.id}').status_code == 200
    assert client.get('/requests/sent').status_code == 200
    assert client.get('/requests/received').status_code == 200


def test_borrower_creates_equipment_request_and_owner_is_notified(client, owner, borrower, equipment):
    login(client, borrower.email)
    response = _send(client, equipment, equipment_request_form())
    assert response.status_code == 302 and response.headers['Location'].endswith('/requests/sent')

    booking = BookingRequest.query.one()
    assert booking.status == STATUS_PENDING
    assert booking.borrower_id == borrower.id and booking.owner_id == owner.id
    assert booking.return_time == '18:00'

    note = Notification.query.filter_by(user_id=owner.id).one()
    assert 'Borrower Two' in note.message and not note.is_read

    assert b'Hammer Drill' in client.get('/requests/sent').data


def test_service_request_stores_service_fields(client, borrower, service):
    login(client, borrower.email)
    assert _send(client, service, service_request_form()).status_code == 302
    booking = BookingRequest.query.one()
    assert booking.duration_hours == 4 and booking.urgency == 'Normal'
    assert booking.pickup_method == 'At My Location'


def test_owner_cannot_request_own_listing(client, owner, equipment):
    login(client, owner.email)
    response = _send(client, equipment, equipment_request_form())
    assert response.status_code == 302 and f'/resources/{equipment.id}' in response.headers['Location']
    assert BookingRequest.query.count() == 0


def test_invalid_form_is_rejected(client, borrower, equipment):
    login(client, borrower.email)
    response = _send(client, equipment, equipment_request_form(start_days=5, end_days=3, purpose='x'))
    assert response.status_code == 200
    assert b'End date cannot be earlier' in response.data
    assert BookingRequest.query.count() == 0


def test_overlapping_request_is_rejected(client, borrower, equipment):
    login(client, borrower.email)
    assert _send(client, equipment, equipment_request_form(3, 5)).status_code == 302
    logout(client)

    other = make_user('third@example.com', 'Third Person')
    login(client, other.email)
    response = _send(client, equipment, equipment_request_form(4, 6))
    assert response.status_code == 200
    assert b'already booked' in response.data
    assert BookingRequest.query.count() == 1

    # Dates after the first booking are fine.
    assert _send(client, equipment, equipment_request_form(6, 7)).status_code == 302
    assert BookingRequest.query.count() == 2


def test_owner_walks_booking_through_its_statuses(client, owner, borrower, equipment):
    login(client, borrower.email)
    _send(client, equipment, equipment_request_form())
    booking_id = BookingRequest.query.one().id
    logout(client)

    login(client, owner.email)
    page = client.get('/requests/received')
    assert b'Borrower Two' in page.data and b'Approve' in page.data

    for action, expected in (('approve', STATUS_APPROVED), ('borrowed', STATUS_BORROWED), ('returned', STATUS_RETURNED)):
        response = client.post(f'/requests/{booking_id}/{action}')
        assert response.status_code == 302
        assert BookingRequest.query.get(booking_id).status == expected

    # Borrower got one notification per transition.
    assert Notification.query.filter_by(user_id=borrower.id).count() == 3
    # Approving again is refused without changing anything.
    client.post(f'/requests/{booking_id}/approve')
    assert BookingRequest.query.get(booking_id).status == STATUS_RETURNED


def test_only_owner_may_approve_and_only_borrower_may_cancel(client, owner, borrower, equipment):
    login(client, borrower.email)
    _send(client, equipment, equipment_request_form())
    booking_id = BookingRequest.query.one().id

    assert client.post(f'/requests/{booking_id}/approve').status_code == 403
    assert client.post(f'/requests/{booking_id}/cancel').status_code == 302
    assert BookingRequest.query.get(booking_id).status == STATUS_CANCELLED
    logout(client)

    login(client, owner.email)
    assert client.post(f'/requests/{booking_id}/cancel').status_code == 403
    assert client.post(f'/requests/{booking_id}/bogus').status_code == 404


def test_received_can_be_filtered_by_listing_and_status(client, owner, borrower, equipment, service):
    login(client, borrower.email)
    _send(client, equipment, equipment_request_form())
    _send(client, service, service_request_form())
    logout(client)

    login(client, owner.email)
    page = client.get(f'/requests/received?resource_id={equipment.id}')
    assert b'Hammer Drill' in page.data and b'House Wiring' not in page.data
    page = client.get('/requests/received?status=approved')
    assert b'No requests with this status' in page.data
