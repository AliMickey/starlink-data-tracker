from flask import (
    Blueprint, render_template, send_file, url_for, current_app
)
from threading import Thread
import schedule, time

# App imports
from starlink.firmware import getFirmwareData

bp = Blueprint('main', __name__)

# Main view for website information
@bp.route('/')
def index():
    # Get firmware data for the past 5 dishy entries
    listDict = getFirmwareData(listType="dishy", range=5)
    return render_template('main/index.html', listDict=listDict)

# View for external links
@bp.route('/info')
def info():
    return render_template('main/info.html')

# View to download database schema/data
@bp.route('/database')
def database():
    return send_file("static/links/databaseBackup.sql", as_attachment=True)

# 404 page not found error
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('main/error-404.html'), 404