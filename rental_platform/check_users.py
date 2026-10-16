from app import app
from models import User

with app.app_context():
    print("Columns:", [c.name for c in User.__table__.columns])
    for u in User.query.all():
        row = {c.name: str(getattr(u, c.name))[:25] for c in User.__table__.columns}
        print(row)