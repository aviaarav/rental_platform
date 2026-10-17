from app.models import BookingRequest, Review
from tests.conftest import equipment_request_form, login, logout


def _returned_booking(client, owner, borrower, equipment):
    login(client, borrower.email)
    client.post(f'/requests/new/{equipment.id}', data=equipment_request_form())
    booking_id = BookingRequest.query.one().id
    logout(client)
    login(client, owner.email)
    for action in ('approve', 'borrowed', 'returned'):
        client.post(f'/requests/{booking_id}/{action}')
    logout(client)
    return booking_id


def test_review_is_blocked_until_returned(client, owner, borrower, equipment):
    login(client, borrower.email)
    client.post(f'/requests/new/{equipment.id}', data=equipment_request_form())
    booking_id = BookingRequest.query.one().id

    response = client.post(f'/reviews/add/{booking_id}', data={'rating': '5'})
    assert response.status_code == 302 and response.headers['Location'].endswith('/requests/sent')
    assert Review.query.count() == 0


def test_borrower_reviews_once_and_rating_shows_on_detail(client, owner, borrower, equipment):
    booking_id = _returned_booking(client, owner, borrower, equipment)
    login(client, borrower.email)

    assert client.get(f'/reviews/add/{booking_id}').status_code == 200
    response = client.post(f'/reviews/add/{booking_id}', data={'rating': '4', 'comment': 'Worked well.'})
    assert response.status_code == 302 and f'/resources/{equipment.id}' in response.headers['Location']

    review = Review.query.one()
    assert review.rating == 4 and review.reviewer_id == borrower.id

    page = client.get(f'/resources/{equipment.id}')
    assert b'Worked well.' in page.data and b'4.0' in page.data

    # A second review for the same booking is refused.
    client.post(f'/reviews/add/{booking_id}', data={'rating': '1'})
    assert Review.query.count() == 1


def test_only_the_borrower_may_review(client, owner, borrower, equipment):
    booking_id = _returned_booking(client, owner, borrower, equipment)
    login(client, owner.email)
    assert client.post(f'/reviews/add/{booking_id}', data={'rating': '5'}).status_code == 403


def test_invalid_rating_is_rejected(client, owner, borrower, equipment):
    booking_id = _returned_booking(client, owner, borrower, equipment)
    login(client, borrower.email)
    response = client.post(f'/reviews/add/{booking_id}', data={'rating': '9'})
    assert response.status_code == 200 and b'Choose a rating' in response.data
    assert Review.query.count() == 0
