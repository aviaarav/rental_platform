from app.extensions import db
from app.models import Notification
from tests.conftest import login


def _notify(user, title, link='/requests/sent'):
    note = Notification(user_id=user.id, title=title, message=f'{title} message', link=link)
    db.session.add(note)
    db.session.commit()
    return note


def test_unread_feed_and_navbar_badge(client, borrower):
    _notify(borrower, 'First')
    _notify(borrower, 'Second')
    login(client, borrower.email)

    data = client.get('/notifications/unread.json').get_json()
    assert data['count'] == 2
    assert [item['title'] for item in data['items']] == ['Second', 'First']
    assert data['items'][0]['link'].endswith('/read')

    page = client.get('/dashboard')
    assert b'data-unread-badge>2<' in page.data


def test_mark_one_read_redirects_to_its_link(client, borrower):
    note = _notify(borrower, 'Approved', link='/requests/sent')
    login(client, borrower.email)

    response = client.post(f'/notifications/{note.id}/read')
    assert response.status_code == 302 and response.headers['Location'].endswith('/requests/sent')
    assert db.session.get(Notification, note.id).is_read

    assert client.get('/notifications/unread.json').get_json()['count'] == 0


def test_external_link_is_not_followed(client, borrower):
    note = _notify(borrower, 'Odd', link='https://evil.example.com')
    login(client, borrower.email)
    response = client.post(f'/notifications/{note.id}/read')
    assert response.headers['Location'].endswith('/notifications')


def test_mark_all_read_and_list_page(client, borrower):
    _notify(borrower, 'A')
    _notify(borrower, 'B')
    login(client, borrower.email)

    page = client.get('/notifications')
    assert page.status_code == 200 and b'Mark all as read (2)' in page.data

    client.post('/notifications/read-all')
    assert Notification.query.filter_by(user_id=borrower.id, is_read=False).count() == 0


def test_cannot_touch_another_users_notification(client, owner, borrower):
    note = _notify(owner, 'Private')
    login(client, borrower.email)
    assert client.post(f'/notifications/{note.id}/read').status_code == 404
