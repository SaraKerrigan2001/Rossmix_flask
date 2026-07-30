"""Vistas principales (index, test_image)."""
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/test-image')
def test_image():
    return render_template('test_image.html')
