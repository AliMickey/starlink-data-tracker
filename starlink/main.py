from flask import (
    Blueprint, render_template, send_file, make_response, request
)

# App imports
from starlink.firmware import getFirmwareData

bp = Blueprint('main', __name__)

# Main view for website information
@bp.route('/')
def index():
    # Get firmware data for the past 5 dishy entries
    listDict = getFirmwareData(listType="dishy", range=5)
    if not request.cookies.get('welcome-message-viewed'):
        res = make_response(render_template('firmware/index.html', listDict=listDict, welcomeMessageCookie='false'))
        res.set_cookie('welcome-message-viewed', 'true', max_age=None)
        return res

    return render_template('firmware/index.html', listDict=listDict, welcomeMessageCookie=request.cookies.get('welcome-message-viewed'))

# View to download database schema/data
@bp.route('/database')
def database():
    return send_file("static/other/databaseBackup.sql", as_attachment=True)

# View for firmware info page
@bp.route('/info')
def info():
    return render_template('main/info.html')

# 404 page not found error
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('main/error-404.html'), 404