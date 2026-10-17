"""Safe image upload helpers."""
import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

from app.constants import TYPE_EQUIPMENT


def folder_for(resource_type):
    """Sub-folder of UPLOAD_FOLDER used for a resource type."""
    return 'equipment' if resource_type == TYPE_EQUIPMENT else 'professional'


def _extension_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_IMAGE_EXTENSIONS']


def _looks_like_image(stream):
    """Check the first bytes of the file (PNG, JPG or WEBP), not just the extension."""
    head = stream.read(16)
    stream.seek(0)
    return (head.startswith(b'\xff\xd8\xff')
            or head.startswith(b'\x89PNG\r\n\x1a\n')
            or (head[:4] == b'RIFF' and head[8:12] == b'WEBP'))


def save_image(file_storage, folder):
    """Save an uploaded image and return the new file name.

    Returns None when no file was chosen. Raises ValueError for a bad file.
    """
    if file_storage is None or file_storage.filename == '':
        return None
    original = secure_filename(file_storage.filename)
    if not original or not _extension_allowed(original):
        raise ValueError('Only PNG, JPG or WEBP images are allowed.')
    if not _looks_like_image(file_storage.stream):
        raise ValueError('The selected file is not a valid image.')

    extension = original.rsplit('.', 1)[1].lower()
    filename = f'{uuid.uuid4().hex}.{extension}'
    target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(target_dir, exist_ok=True)
    file_storage.save(os.path.join(target_dir, filename))
    return filename


def delete_image(folder, filename):
    """Remove an old image file (ignored when it does not exist)."""
    if not filename:
        return
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, os.path.basename(filename))
    try:
        os.remove(path)
    except OSError:
        pass