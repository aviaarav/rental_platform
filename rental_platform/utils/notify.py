"""Helpers for activity logs and popup notifications."""
from extensions import db
from models import ActivityLog, Notification


def log_activity(action, details='', user_id=None, commit=True):
    db.session.add(ActivityLog(user_id=user_id, action=action, details=(details or '')[:255]))
    if commit:
        db.session.commit()


def create_notification(user_id, title, message, link=None, commit=True):
    db.session.add(Notification(user_id=user_id, title=title[:120], message=message[:255], link=link))
    if commit:
        db.session.commit()