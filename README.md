# Rental Platform

Flask app for renting equipment and booking services across Tamil Nadu districts.

## Layout

```
backend/            all Python: Flask package, migrations, entry points
  app/              the Flask package
    __init__.py     create_app() factory
    config.py       Development / Production / Testing settings
    constants.py    roles, resource types, booking statuses
    cli.py          flask seed-admin, flask check-users
    models/         one file per table
    routes/         one file per blueprint
    services/       db-touching helpers (booking, notify, uploads)
    utils/          pure helpers (decorators, geo)
    data/           static reference data (categories, Tamil Nadu locations)
  migrations/       Flask-Migrate / Alembic schema history
  tests/            pytest suite (in-memory sqlite)
  instance/         runtime data, gitignored (sqlite db, user uploads)
  requirements.txt  requirements-dev.txt
  run.py            dev entry point
  wsgi.py           production entry point (gunicorn wsgi:app)
frontend/           everything the browser receives
  templates/        Jinja templates
  static/           css, js
docs/plans/         design and refactor plans
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env        # then edit SECRET_KEY and ADMIN_* values

cd backend
flask --app app db upgrade  # create or migrate the database
flask --app app seed-admin  # create the default admin from ADMIN_EMAIL / ADMIN_PASSWORD
flask --app app run --debug # or: python run.py
```

Open http://127.0.0.1:5000.

## Features

- Users register, log in, and manage a profile (details and password).
- Owners list equipment for rent or professional services, with optional coordinates.
- Borrowers browse by keyword, category, district, date range and distance, then send a
  booking request. Date conflicts with pending, approved or borrowed bookings are refused.
- Owners approve or reject requests, then mark them borrowed / started and returned / completed.
  Borrowers can cancel while pending or approved.
- After a booking is returned, the borrower can leave one review; ratings show on the listing.
- Every booking change creates an in-app notification. The navbar badge and popup toasts
  poll `/notifications/unread.json` every 30 seconds.
- Admins have a separate login and dashboard.

## Tests and lint

```bash
pip install -r backend/requirements-dev.txt
cd backend
pytest            # runs tests/ against an in-memory database
ruff check .      # lint; `ruff check --fix .` sorts imports
```

## Database changes

Schema changes go through Flask-Migrate. After editing a model:

```bash
cd backend
flask --app app db migrate -m "describe the change"   # writes migrations/versions/<id>_*.py
flask --app app db upgrade                            # applies it
```

Uploaded images are stored in `backend/instance/uploads/` and served at
`/uploads/<type>/<file>`. Set `UPLOAD_FOLDER` to move them elsewhere.

## Configuration

All settings live in `backend/app/config.py` and are read from the environment
or the repo-root `.env` file. `FLASK_CONFIG` selects `development` (default),
`production` or `testing`. `FRONTEND_DIR` overrides where templates and static
files are loaded from.
