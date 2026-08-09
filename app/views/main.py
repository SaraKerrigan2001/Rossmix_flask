"""Vistas principales (index, test_image)."""
from flask import Blueprint, render_template
from app.extensions import cache

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@cache.cached(timeout=120)
def index():
    return render_template('index.html')


@main_bp.route('/test-image')
@cache.cached(timeout=120)
def test_image():
    return render_template('test_image.html')
