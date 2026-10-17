from app.extensions import db
from app.models import User
from tests.conftest import DISTRICT, PASSWORD, TALUK, login, logout


def test_profile_page_renders(client, borrower):
    login(client, borrower.email)
    page = client.get('/profile')
    assert page.status_code == 200
    assert b'Borrower Two' in page.data and b'Change Password' in page.data


def test_update_details(client, borrower):
    login(client, borrower.email)
    response = client.post('/profile', data={
        'full_name': 'Renamed Person', 'phone': '9111111111',
        'district': DISTRICT, 'taluk': TALUK, 'address': '99 New Street',
    }, follow_redirects=True)
    assert response.status_code == 200 and b'Profile updated' in response.data

    user = db.session.get(User, borrower.id)
    assert user.full_name == 'Renamed Person' and user.phone == '9111111111' and user.address == '99 New Street'


def test_invalid_details_are_rejected(client, borrower):
    login(client, borrower.email)
    response = client.post('/profile', data={
        'full_name': 'ab', 'phone': '12', 'district': 'Nowhere', 'taluk': 'Nowhere', 'address': '',
    })
    assert response.status_code == 200
    assert b'Phone number must be 10 digits' in response.data
    assert db.session.get(User, borrower.id).full_name == 'Borrower Two'


def test_change_password_requires_current_password(client, borrower):
    login(client, borrower.email)
    response = client.post('/profile/password', data={
        'current_password': 'wrong', 'new_password': 'newpass123', 'confirm_password': 'newpass123',
    }, follow_redirects=True)
    assert b'Current password is incorrect' in response.data
    assert db.session.get(User, borrower.id).check_password(PASSWORD)


def test_change_password_then_login_with_new_one(client, borrower):
    login(client, borrower.email)
    client.post('/profile/password', data={
        'current_password': PASSWORD, 'new_password': 'newpass123', 'confirm_password': 'newpass123',
    })
    logout(client)
    assert login(client, borrower.email, 'wrong').request.path == '/auth/login'
    assert login(client, borrower.email, 'newpass123').request.path == '/dashboard'
