from flask import (
    Blueprint, render_template, send_file, current_app, make_response, request
)

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('main/index.html')

# View to download database schema/data
@bp.route('/database')
def database():
    return send_file(current_app.root_path + "/static/other/databaseBackup.sql", as_attachment=True)

# View for info page
@bp.route('/info')
def info():
    return render_template('main/info.html')

# View for priavcy policy page
@bp.route('/privacypolicy')
def privacypolicy():
    return render_template('main/privacypolicy.html')

# 404 page not found error
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('main/error-404.html'), 404