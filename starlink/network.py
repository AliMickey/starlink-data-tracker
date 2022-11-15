from flask import (
    Blueprint, flash, redirect, render_template, request, abort, url_for, current_app, g
)

# App imports
from starlink.db import get_db
from starlink.auth import login_required

bp = Blueprint('network', __name__, url_prefix='/network')

# Dashboard for firmware page
@bp.route('/')
def index():
    ip = request.headers.get('cf-connecting-ip')

    return render_template('network/index.html', ip=ip)

# View to show all firmware versions for a specific hardware/software type
@bp.route('/<string:listType>', methods = ['GET', 'POST'])
def list(listType):
    if request.method == 'POST':
        db = get_db()
           
        return redirect(request.referrer)