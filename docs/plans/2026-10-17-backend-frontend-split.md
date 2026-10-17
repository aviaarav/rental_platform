# Backend / Frontend folder split (keep Jinja)

Date: 2026-10-17
Status: all four phases applied (branches refactor/phase-1-hygiene .. refactor/phase-4-features, each stacked on the previous)

## Goal

Separate all Python into `backend/` and all templates, CSS and JS into `frontend/`,
while Flask keeps rendering pages with Jinja. No API rewrite, no SPA.

## Target structure

```
rental_platform/                      # repo root
├── .gitignore
├── .env.example
├── README.md
│
├── backend/                          # everything Python; deployable on its own
│   ├── requirements.txt
│   ├── requirements-dev.txt          # pytest, ruff
│   ├── run.py                        # dev entry: create_app().run(debug=True)
│   ├── wsgi.py                       # gunicorn entry: app = create_app()
│   │
│   ├── app/                          # the Flask package
│   │   ├── __init__.py               # create_app(); points Flask at ../frontend
│   │   ├── config.py                 # Base / Development / Production / Testing (inside the package so imports never depend on cwd)
│   │   ├── extensions.py             # db, login_manager
│   │   ├── constants.py              # ROLE_*, TYPE_*, status strings
│   │   ├── cli.py                    # flask seed-admin, flask check-users
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── resource.py
│   │   │   ├── booking.py
│   │   │   ├── review.py
│   │   │   ├── notification.py
│   │   │   └── activity_log.py
│   │   ├── routes/                   # one file per blueprint
│   │   │   ├── __init__.py           # register_blueprints (all nine)
│   │   │   ├── main.py  auth.py  dashboard.py  profile.py  resource.py
│   │   │   ├── request.py  review.py  notifications.py  admin.py
│   │   │   └── uploads.py            # GET /uploads/<path>  (serves user images)
│   │   ├── services/                 # db-touching logic
│   │   │   ├── booking.py
│   │   │   ├── notify.py
│   │   │   └── uploads.py
│   │   ├── utils/                    # pure helpers
│   │   │   ├── decorators.py
│   │   │   └── geo.py
│   │   └── data/
│   │       ├── categories.py
│   │       └── tn_locations.py
│   │
│   ├── instance/                     # gitignored
│   │   ├── rental.db
│   │   └── uploads/                  # user-uploaded images (moved out of static/)
│   ├── migrations/                   # Flask-Migrate, phase 3
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_resources.py
│       └── test_booking.py
│
└── frontend/                         # everything the browser receives
    ├── templates/                    # unchanged tree
    │   ├── base.html  base_admin.html  home.html  dashboard.html
    │   ├── profile.html  choose_role.html
    │   ├── partials/  auth/  admin/  resources/  requests/  reviews/
    └── static/
        ├── css/style.css
        └── js/  main.js  browse.js  location.js  taluk.js  notifications.js
```

## How Flask finds the frontend

`backend/app/config.py` resolves the paths; `backend/app/__init__.py` uses them:

```python
from pathlib import Path
from flask import Flask

BACKEND_DIR = Path(__file__).resolve().parents[1]           # backend/
FRONTEND_DIR = Path(os.environ.get('FRONTEND_DIR', BACKEND_DIR.parent / 'frontend'))

def create_app(config_class=None):
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / 'templates'),
        static_folder=str(FRONTEND_DIR / 'static'),
        instance_relative_config=True,
    )
    app.config.from_object(config_class or 'config.DevelopmentConfig')
    ...
```

`FRONTEND_DIR` is overridable by env so a container can mount the frontend anywhere.
`url_for('static', ...)` keeps working unchanged in all 19 template references.

## Uploads move out of static/

Today user images are written to `static/uploads/<type>/` and served as static files.
After the split `static/` is frontend source, so runtime user data should not live there.

- `UPLOAD_FOLDER` becomes `backend/instance/uploads` (gitignored, survives deploys).
- New blueprint `routes/uploads.py`:

  ```python
  uploads_bp = Blueprint('uploads', __name__, url_prefix='/uploads')

  @uploads_bp.get('/<path:filename>')
  def serve(filename):
      return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
  ```

- `Resource.image_path` returns `f'{folder}/{self.image}'` (drops the `uploads/` prefix).
- Three templates change `url_for('static', filename=r.image_path)` to
  `url_for('uploads.serve', filename=r.image_path)`:
  `resources/_image_field.html`, `resources/detail.html`, `resources/my_items.html`.
- `services/uploads.py` needs no change beyond reading the new `UPLOAD_FOLDER`.

## Running

```
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env          # edit SECRET_KEY, ADMIN_* values
flask --app app run --debug         # or: python run.py
pytest                              # tests use TestingConfig + in-memory sqlite
```

## Phases (each one a commit, app runnable after each)

### Phase 1: hygiene
- Add `.gitignore`: `backend/instance/`, `__pycache__/`, `*.pyc`, `.env`, `.venv/`.
- `git rm --cached` the tracked `rental.db` and `.pyc` files.
- Add `.env.example`; read `SECRET_KEY`, `DATABASE_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
  from env in `app.py` with current values as dev defaults.

### Phase 2: the split (one sitting; touches every import)
- `git mv rental_platform/templates frontend/templates`
- `git mv rental_platform/static    frontend/static`
- `git mv rental_platform            backend/app`
- Move `requirements.txt` to `backend/`, add `config.py`, `run.py`, `wsgi.py`.
- Move `create_app` from `app.py` into `app/__init__.py` with the template/static paths above.
- Rewrite flat imports to package imports in every file:
  `from extensions import db`  ->  `from app.extensions import db`
  (same for `models`, `routes`, `utils`, `data`).
- Register `resource_bp` (defined but never registered today).
- Verify: `cd backend && flask --app app run`, open `/`, `/auth/login`, `/resources/`.

### Phase 3: uploads + models + services
- Add `routes/uploads.py`, change `UPLOAD_FOLDER`, update the three templates.
- Split `models.py` into `models/`; extract `constants.py`.
- Move `utils/booking.py`, `utils/notify.py`, `utils/uploads.py` to `services/`.
- Replace `seed_admin()` on boot and `check_users.py` with commands in `cli.py`.
  (`backend/scripts/` dropped; `flask check-users` replaces the script.)
- Add Flask-Migrate; initial migration replaces `db.create_all()`.

### Phase 4: fill and test
- Implement the four stub blueprints: `profile`, `request`, `review`, `notifications`.
  The matching templates were empty files, so the pages were built from scratch
  following the existing Bootstrap layout; the navbar, dashboard, My Items and
  detail page placeholders now link to them. `partials/_flash.html` (also empty)
  renders flashed messages. `static/js/notifications.js` polls the unread feed.
- Add `tests/` with a `conftest.py` app fixture (in-memory sqlite, two users, a
  listing) and tests for auth, booking requests and status transitions, reviews,
  notifications and profile. `pytest.ini` sets `pythonpath = .`; `pyproject.toml`
  configures ruff.
- Not done: the admin pages (`admin/users.html`, `bookings.html`, `resources.html`,
  `logs.html`, `user_detail.html`) are still empty files and the admin sidebar
  links still point to `#`. That is a separate stage.

## Deliberately not done
- No JSON API, no React/Vue. Jinja stays. A future SPA can still live in `frontend/`
  by replacing `templates/` and `static/` with a build output directory.
- Routes stay as flat files, not per-blueprint packages. ~1,100 lines does not need it.
