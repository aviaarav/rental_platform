from flask import Blueprint, jsonify, render_template, request

from app.data.tn_locations import get_taluks

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return render_template('home.html')


@main_bp.route('/get-started')
def choose_role():
    return render_template('choose_role.html')


@main_bp.route('/api/taluks')
def taluks():
    """JSON list of taluks for the dependent District -> Taluk dropdown."""
    district = request.args.get('district', '')
    return jsonify(get_taluks(district))