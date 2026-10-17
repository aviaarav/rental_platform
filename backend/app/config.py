"""Configuration classes.

Pick one with FLASK_CONFIG=development|production|testing (default: development).
Secrets and deploy-specific values come from the environment or the repo-root .env
file (see .env.example). Values already in the environment win over the file.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]      # backend/
REPO_DIR = BACKEND_DIR.parent                           # repo root

load_dotenv(REPO_DIR / '.env')

# Where Flask finds templates/ and static/. Overridable so a container can mount
# the frontend anywhere.
FRONTEND_DIR = Path(os.environ.get('FRONTEND_DIR', REPO_DIR / 'frontend'))


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret-key-before-deployment')

    # Relative sqlite paths resolve inside backend/instance/.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///rental.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024                # 5 MB uploads
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    # Phase 2 keeps user uploads under frontend/static/uploads (gitignored) so the
    # existing url_for('static', ...) references keep working. Phase 3 moves them
    # to backend/instance/uploads behind a dedicated route.
    UPLOAD_FOLDER = str(FRONTEND_DIR / 'static' / 'uploads')

    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@rentserve.in')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@123')


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


CONFIGS = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def get_config(name=None):
    """Return the config class for `name`, else for FLASK_CONFIG, else development."""
    return CONFIGS[name or os.environ.get('FLASK_CONFIG', 'development')]
