"""Shared fixtures: an app on an in-memory database, a client, two users and a listing."""
from datetime import date, timedelta

import pytest

from app import create_app
from app.config import TestingConfig
from app.constants import ROLE_USER, TYPE_EQUIPMENT, TYPE_PROFESSIONAL
from app.extensions import db as _db
from app.models import Resource, User

PASSWORD = 'secret123'
DISTRICT, TALUK = 'Coimbatore', 'Coimbatore North'


@pytest.fixture
def app(tmp_path):
    app = create_app(TestingConfig)
    app.config['UPLOAD_FOLDER'] = str(tmp_path / 'uploads')
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(email, name='Test User'):
    user = User(full_name=name, email=email, phone='9876543210', district=DISTRICT, taluk=TALUK,
                address='12 Main Street', role=ROLE_USER)
    user.set_password(PASSWORD)
    _db.session.add(user)
    _db.session.commit()
    return user


def make_resource(owner, kind=TYPE_EQUIPMENT, name='Hammer Drill', **overrides):
    fields = dict(owner_id=owner.id, resource_type=kind, name=name, category='Power Tools',
                  description='A powerful hammer drill for concrete walls.', district=DISTRICT, taluk=TALUK,
                  price=500, charge_type='Per Day', availability='Available')
    if kind == TYPE_EQUIPMENT:
        fields.update(condition='Good', pickup_method="Owner's Home")
    else:
        fields.update(category='Electrician', charge_type='Per Hour', experience=5)
    fields.update(overrides)
    resource = Resource(**fields)
    _db.session.add(resource)
    _db.session.commit()
    return resource


@pytest.fixture
def owner(app):
    return make_user('owner@example.com', 'Owner One')


@pytest.fixture
def borrower(app):
    return make_user('borrower@example.com', 'Borrower Two')


@pytest.fixture
def equipment(owner):
    return make_resource(owner)


@pytest.fixture
def service(owner):
    return make_resource(owner, kind=TYPE_PROFESSIONAL, name='House Wiring')


def login(client, email, password=PASSWORD):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)


def logout(client):
    return client.get('/auth/logout', follow_redirects=True)


def future(days):
    return (date.today() + timedelta(days=days)).isoformat()


def equipment_request_form(start_days=3, end_days=5, **overrides):
    form = {
        'start_date': future(start_days), 'end_date': future(end_days),
        'purpose': 'Home renovation', 'purpose_details': 'Drilling anchor holes',
        'request_district': DISTRICT, 'request_taluk': TALUK, 'address': '45 Lake View Road',
        'service_time': '09:00', 'return_time': '18:00', 'pickup_method': "Owner's Home",
    }
    form.update(overrides)
    return form


def service_request_form(start_days=3, end_days=3, **overrides):
    form = {
        'start_date': future(start_days), 'end_date': future(end_days),
        'purpose': 'Fix wiring', 'request_district': DISTRICT, 'request_taluk': TALUK,
        'address': '45 Lake View Road', 'service_time': '10:00', 'duration_hours': '4',
        'urgency': 'Normal', 'pickup_method': 'At My Location',
    }
    form.update(overrides)
    return form
