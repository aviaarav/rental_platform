def register_blueprints(app):
    """Every stage adds its blueprints here."""
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.resource import resource_bp
    from app.routes.uploads import uploads_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(admin_bp)
