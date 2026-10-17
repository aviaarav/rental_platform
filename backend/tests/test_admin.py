from app.constants import STATUS_APPROVED
from app.extensions import db
from app.models import ActivityLog, BookingRequest, Notification, Resource, User
from tests.conftest import admin_login, equipment_request_form, login, make_resource, make_user

ADMIN_PAGES = ['/admin/dashboard', '/admin/users', '/admin/resources', '/admin/bookings', '/admin/logs']


def test_admin_pages_need_an_admin(client, borrower, admin):
    for path in ADMIN_PAGES:
        response = client.get(path)
        assert response.status_code == 302 and '/auth/admin-login' in response.headers['Location']

    login(client, borrower.email)
    for path in ADMIN_PAGES:
        response = client.get(path)
        assert response.status_code == 302 and response.headers['Location'].endswith('/dashboard')
    assert client.post(f'/admin/users/{borrower.id}/block').status_code == 302
    assert not db.session.get(User, borrower.id).is_blocked


def test_admin_pages_render_with_data(client, owner, borrower, equipment, admin):
    login(client, borrower.email)
    client.post(f'/requests/new/{equipment.id}', data=equipment_request_form())
    client.get('/auth/logout')

    admin_login(client, admin)
    for path in ADMIN_PAGES + [f'/admin/users/{owner.id}', '/admin/bookings?status=pending',
                               '/admin/resources?type=Equipment&visibility=visible', '/admin/logs?q=booking']:
        assert client.get(path).status_code == 200, path

    page = client.get('/admin/dashboard').data
    assert b'Hammer Drill' in page and b'Borrower Two' in page
    page = client.get('/admin/users?q=borrower').data
    assert b'Borrower Two' in page and b'Owner One' not in page
    assert client.get(f'/admin/users/{admin.id}').status_code == 404


def test_blocking_a_user_logs_them_out(app, client, borrower, admin):
    user_client = app.test_client()
    login(user_client, borrower.email)
    assert user_client.get('/dashboard').status_code == 200

    admin_login(client, admin)
    response = client.post(f'/admin/users/{borrower.id}/block', data={'next': '/admin/users?status=blocked'})
    assert response.status_code == 302 and response.headers['Location'].endswith('/admin/users?status=blocked')
    assert db.session.get(User, borrower.id).is_blocked
    assert ActivityLog.query.filter_by(action='User blocked').count() == 1

    response = user_client.get('/dashboard', follow_redirects=True)
    assert b'Your account has been blocked' in response.data
    assert user_client.get('/dashboard').status_code == 302          # session is gone
    assert b'blocked' in login(user_client, borrower.email).data        # and login is refused

    client.post(f'/admin/users/{borrower.id}/unblock')
    assert not db.session.get(User, borrower.id).is_blocked
    assert login(user_client, borrower.email).request.path == '/dashboard'


def test_block_rejects_unknown_action_and_external_next(client, borrower, admin):
    admin_login(client, admin)
    assert client.post(f'/admin/users/{borrower.id}/delete').status_code == 404
    response = client.post(f'/admin/users/{borrower.id}/block', data={'next': 'https://evil.example.com'})
    assert response.headers['Location'].endswith(f'/admin/users/{borrower.id}')


def test_hiding_a_listing_removes_it_from_other_users(client, owner, borrower, equipment, admin):
    admin_login(client, admin)
    client.post(f'/admin/resources/{equipment.id}/hide')
    assert db.session.get(Resource, equipment.id).is_hidden
    note = Notification.query.filter_by(user_id=owner.id).one()
    assert 'hidden' in note.title.lower()
    client.get('/auth/logout')

    login(client, borrower.email)
    assert b'Hammer Drill' not in client.get('/resources/browse').data
    assert client.get(f'/resources/{equipment.id}').status_code == 404
    client.get('/auth/logout')

    # The owner still sees it, and the admin can unhide it.
    login(client, owner.email)
    assert client.get(f'/resources/{equipment.id}').status_code == 200
    client.get('/auth/logout')
    admin_login(client, admin)
    client.post(f'/admin/resources/{equipment.id}/unhide')
    assert not db.session.get(Resource, equipment.id).is_hidden
    assert client.post(f'/admin/resources/{equipment.id}/burn').status_code == 404


def test_bookings_and_logs_filters(client, owner, borrower, equipment, admin):
    make_resource(owner, kind='Professional', name='House Wiring')
    login(client, borrower.email)
    client.post(f'/requests/new/{equipment.id}', data=equipment_request_form())
    booking = BookingRequest.query.one()
    booking.status = STATUS_APPROVED
    db.session.commit()
    client.get('/auth/logout')

    admin_login(client, admin)
    assert b'Hammer Drill' in client.get('/admin/bookings?status=approved').data
    assert b'No bookings with this status' in client.get('/admin/bookings?status=pending').data
    assert b'Hammer Drill' not in client.get('/admin/bookings?q=wiring').data
    assert b'House Wiring' in client.get('/admin/resources?q=wiring').data
    assert b'Booking requested' in client.get('/admin/logs?q=requested').data
    assert b'No activity matches' in client.get('/admin/logs?q=zzzz').data


def test_users_list_paginates(client, admin):
    for i in range(25):
        make_user(f'person{i}@example.com', f'Person {i:02d}')
    admin_login(client, admin)
    first = client.get('/admin/users').data
    second = client.get('/admin/users?page=2').data
    assert b'25 total, page 1 of 2' in first and b'page 2 of 2' in second
