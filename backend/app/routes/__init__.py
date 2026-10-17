def register_blueprints(app):
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.main import main_bp
    from app.routes.notifications import notifications_bp
    from app.routes.profile import profile_bp
    from app.routes.request import request_bp
    from app.routes.resource import resource_bp
    from app.routes.review import review_bp
    from app.routes.uploads import uploads_bp

    for blueprint in (main_bp, auth_bp, dashboard_bp, profile_bp, resource_bp, request_bp,
                      review_bp, notifications_bp, uploads_bp, admin_bp):
        app.register_blueprint(blueprint)
