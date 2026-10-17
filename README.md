# Rental Platform

Flask app for renting equipment and booking services across Tamil Nadu districts.

## Layout

```
backend/            all Python: Flask package, config, entry points, scripts, tests
  app/              the Flask package (factory in app/__init__.py)
  instance/         runtime data, gitignored (sqlite db)
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
flask --app app run --debug # or: python run.py
```

Open http://127.0.0.1:5000. A default admin is created on first start using
`ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env`.

## Configuration

All settings live in `backend/app/config.py` and are read from the environment
or the repo-root `.env` file. `FLASK_CONFIG` selects `development` (default),
`production` or `testing`. `FRONTEND_DIR` overrides where templates and static
files are loaded from.
