from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for, flash
)
from werkzeug.security import check_password_hash
import functools

# App imports
from starlink.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Global authentication checker
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None: return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

# Set session user id
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()


# View to login to the system
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()   
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user is None or not check_password_hash(user['password'], password):
            flash("Incorrect username or password. Please try again.", "danger")
            return redirect(url_for('auth.login'))
        else:
            session.clear()
            session['user_id'] = user['id']
        return redirect(url_for('main.index'))
           
    return render_template('auth/login.html')
    
# View to clear session
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))