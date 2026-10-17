"""Print every user row and the User table columns.

Run from backend/:  python scripts/check_users.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # make `app` importable

from app import create_app          # noqa: E402
from app.models import User         # noqa: E402

app = create_app()

with app.app_context():
    print("Columns:", [c.name for c in User.__table__.columns])
    for u in User.query.all():
        row = {c.name: str(getattr(u, c.name))[:25] for c in User.__table__.columns}
        print(row)
