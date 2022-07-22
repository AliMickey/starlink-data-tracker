from flask import (
    Blueprint, render_template, send_file, current_app, make_response, request
)

import requests

# App imports
from starlink.notifications import sendEmail

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if not request.cookies.get('welcome-message-viewed'):
        res = make_response(render_template('main/index.html', welcomeMessageCookie='false'))
        res.set_cookie('welcome-message-viewed', 'true', max_age=None)
        return res

    return render_template('main/index.html', welcomeMessageCookie=request.cookies.get('welcome-message-viewed'))

# View to download database schema/data
@bp.route('/database')
def database():
    return send_file(current_app.root_path + "/static/other/databaseBackup.sql", as_attachment=True)

# View for firmware info page
@bp.route('/info')
def info():
    #x = requests.post('http://0.0.0.0:8080/new-firmware?firmware=test')
    return render_template('main/info.html')

# 404 page not found error
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('main/error-404.html'), 404