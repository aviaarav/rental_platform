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
  instance/         runtime data, gitignored (sqlite db, user uploads)
  requirements.txt
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
