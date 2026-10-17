"""Custom Flask CLI commands.  Run from backend/:  flask --app app <command>

Database schema commands come from Flask-Migrate:  flask --app app db --help
"""
import click
from flask import current_app
from flask.cli import with_appcontext

from app.constants import ROLE_ADMIN
from app.extensions import db
from app.models import User


@click.command('seed-admin')
@with_appcontext
def seed_admin():
    """Create the default administrator from ADMIN_EMAIL / ADMIN_PASSWORD if missing."""
    email = current_app.config['ADMIN_EMAIL']
    password = current_app.config['ADMIN_PASSWORD']
    if User.query.filter_by(email=email).first():
        click.echo(f'Admin {email} already exists; nothing to do.')
        return
    admin = User(full_name='Administrator', email=email, phone='0000000000',
                 district='Coimbatore', taluk='Coimbatore North', address='Admin Office', role=ROLE_ADMIN)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f'Default admin created: {email}  (change this password later)')


@click.command('check-users')
@with_appcontext
def check_users():
    """Print the User table columns and every user row."""
    columns = [c.name for c in User.__table__.columns]
    click.echo(f'Columns: {columns}')
    for user in User.query.order_by(User.id).all():
        row = {c: str(getattr(user, c))[:25] for c in columns}
        click.echo(row)


def register_commands(app):
    app.cli.add_command(seed_admin)
    app.cli.add_command(check_users)
