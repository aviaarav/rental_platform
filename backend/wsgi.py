"""Production entry point:  cd backend && gunicorn wsgi:app"""
from app import create_app

app = create_app()
