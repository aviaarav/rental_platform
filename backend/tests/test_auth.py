from app.models import User
from tests.conftest import DISTRICT, PASSWORD, TALUK, login, logout


def test_home_and_login_pages_render(client):
    assert client.get('/').status_code == 200
    assert client.get('/auth/login').status_code == 200
    assert client.get('/auth/register').status_code == 200


def test_register_then_login_reaches_dashboard(client):
    response = client.post('/auth/register', data={
        'full_name': 'New Person', 'email': 'new@example.com', 'phone': '9000000000',
        'password': PASSWORD, 'confirm_password': PASSWORD,
        'district': DISTRICT, 'taluk': TALUK, 'address': '1 Some Street',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert User.query.filter_by(email='new@example.com').count() == 1

    response = login(client, 'new@example.com')
    assert response.request.path == '/dashboard'
    assert b'Welcome, New Person' in response.data


def test_wrong_password_is_rejected(client, owner):
    response = login(client, owner.email, 'wrong-password')
    assert response.request.path == '/auth/login'
    assert b'Invalid email or password' in response.data


def test_protected_page_redirects_anonymous_user(client):
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_logout(client, owner):
    login(client, owner.email)
    response = logout(client)
    assert response.request.path == '/'
    assert client.get('/dashboard').status_code == 302
