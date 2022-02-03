from flask import (
    Blueprint, g, render_template
)

bp = Blueprint('main', __name__)

# Main view for website information
@bp.route('/')
def index():
    return render_template('main/index.html')

# View for external links
@bp.route('/links')
def links():
    return render_template('main/links.html')

# 404 page not found error
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404