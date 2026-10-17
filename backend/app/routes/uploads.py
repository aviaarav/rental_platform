"""Serve user-uploaded images from UPLOAD_FOLDER, which lives outside the frontend static tree."""
from flask import Blueprint, current_app, send_from_directory

uploads_bp = Blueprint('uploads', __name__, url_prefix='/uploads')


@uploads_bp.get('/<path:filename>')
def serve(filename):
    """Return one uploaded file; send_from_directory refuses paths that escape UPLOAD_FOLDER."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
