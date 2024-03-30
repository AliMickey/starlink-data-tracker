from flask import (
    Blueprint, flash, render_template, current_app
)

bp = Blueprint('shop', __name__, url_prefix='/shop')

# Dashboard for shop page
@bp.route('/')
def index():
    return render_template('shop/index.html', amazonAffiliateId=current_app.config['AMAZON_AFFILIATE_ID'])