from flask import (
    Blueprint, current_app, g, redirect, render_template, request, session, url_for, flash
)
from werkzeug.security import check_password_hash, generate_password_hash
import functools, re, uuid, requests
from datetime import datetime
from profanity_check import predict

# App imports
from starlink.db import get_db
from starlink.notifications import sendEmail

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

# View to register a new user
@bp.route('/register', methods=('GET', 'POST'))
def register():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        passwordRepeat = request.form['passwordRepeat']
        captcha = request.form['h-captcha-response']
        db = get_db()

        userEmailCheck = db.execute('SELECT EXISTS (SELECT 1 FROM users WHERE email = ? LIMIT 1)', (email,)).fetchone()[0]
        userUsernameCheck =  db.execute('SELECT EXISTS (SELECT 1 FROM users WHERE username = ? LIMIT 1)', (username,)).fetchone()[0]
        emailRegex = '''(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'''
        
        # Captcha verification
        hcapcthaSecret = current_app.config['HCAPCTHA_KEY']
        response = requests.post(url = "https://hcaptcha.com/siteverify", data = {'secret': hcapcthaSecret, 'response': captcha}).json()
        
        if not response['success']:
            error = "Invalid captcha. Please try again"     
        elif not email: 
            error = "Email address is required"
        elif not re.search(emailRegex, email):
            error = "Email address is not valid"
        elif userEmailCheck == 1:
            error = "Email address is already registered"
        elif not username:
            error = "Username is required"
        elif userUsernameCheck == 1:
            error = "Username is already taken"
        elif predict([username]) == 1:
            error = "Username contains profanity"
        elif not password or not passwordRepeat:
            error = "Password is required"
        elif len(password) < 8:
            error = "Password must be a minimum of 8 digits"
        elif password != passwordRepeat:
            error = "Passwords do not match"

        if error is None:
            db.execute(
                'INSERT INTO users (email, username, password, role) VALUES (?, ?, ?, ?)', (email, username, generate_password_hash(password), "user"))
            db.commit()
            sendEmail(email, "Welcome to Starlink Data Tracker", f"Hi {username}, welcome to Starlink Data Tracker.")
            flash("User registered successfully", "success")
            return redirect(url_for('auth.login'))
        else:
            flash(error, "warning")

    return render_template('auth/register.html')

# View to login to the system
@bp.route('/login', methods=('GET', 'POST'))
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()   
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user is None or not check_password_hash(user['password'], password):
            error = "Incorrect email address or password. Please try again."
        
        if error:
            flash(error, "warning")
        else:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('main.index'))
           
    return render_template('auth/login.html')

# View to request a new password link
@bp.route('/account', methods=('GET', 'POST'))
def account():
    error = None

    return render_template('auth/account.html')


# View to request a new password link
@bp.route('/forgot-password', methods=('GET', 'POST'))
def forgotPassword():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        db = get_db()   
        # Get user id for email if exists
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user:
            userID = user['id']
            # Check if user has used key or has already requested for a password reset within last 24 hours
            resetPassDetails = db.execute('SELECT reset_key, datetime(date_time), activated FROM users_password_reset WHERE user_id = ?', (userID,)).fetchone()
            # Send the same key again
            if resetPassDetails and checkPasswordResetValidity(resetPassDetails[1], resetPassDetails['activated']):
                resetKey = resetPassDetails['reset_key']

            else:
                # Generate and send a new key
                resetKey = uuid.uuid4()
                db.execute('INSERT INTO users_password_reset (reset_key, user_id, date_time, activated) VALUES (?, ?, ?, ?) ', 
                    (str(resetKey), userID, datetime.utcnow(), False))
                db.commit()

            sendEmail(email, "Reset password", f"Use the following link to reset your password for Starlink Data Tracker. https://starlinkversions.com/auth/reset-password/{resetKey}")
        
        # Generic message to prevent brute email validity checks
        error = "If the provided email exists, you will soon receive an email with instructions. Please check your spam folder."
        
        if error:
            flash(error, "success")

    return render_template('auth/forgot-password.html')

# View to reset password via uuid
@bp.route('/reset-password/<string:resetKey>', methods=('GET', 'POST'))
def resetPassword(resetKey):
    error = None
    db = get_db()          
    resetPassDetails = db.execute('SELECT user_id, datetime(date_time), activated FROM users_password_reset WHERE reset_key = ?', (resetKey,)).fetchone()
    
    if request.method == 'GET':
        if resetPassDetails and checkPasswordResetValidity(resetPassDetails[1], resetPassDetails['activated']): 
            return render_template('auth/reset-password.html', resetKey=resetKey)
        else:
            error = "Either the url is no longer valid, or you are here by mistake."
        
        if error:
            flash(error, "warning")

    elif request.method == 'POST':
        if resetPassDetails and checkPasswordResetValidity(resetPassDetails[1], resetPassDetails['activated']):
            password = request.form['password']
            passwordRepeat = request.form['passwordRepeat']

            if not password or not passwordRepeat:
                error = 'Password is required'
            elif len(password) < 8:
                error = "Password must be a minimum of 8 digits"
            elif password != passwordRepeat:
                error = 'Passwords do not match'

            if error is None:
                db.execute(
                    'UPDATE users SET password = ? WHERE id = ?',
                    (generate_password_hash(password), resetPassDetails['user_id']))
                db.execute(
                    'UPDATE users_password_reset SET activated = 1 WHERE reset_key = ?',
                    (resetKey,))
                db.commit() 
                sendEmail(db.execute('SELECT email FROM users WHERE id = ?', (resetPassDetails['user_id'],)).fetchone()[0], "Account activity", "Your password has been succesfully reset.")
                session.clear()
                flash("Password reset successfully", "success") 
                return redirect(url_for('auth.login'))
            else:
                flash(error, "warning")
    
    return render_template('auth/reset-password.html', error=error)      
    
# View to clear session
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))


# Function to check if reset password key is still valid       
def checkPasswordResetValidity(genTime, activated):
    generatedDateTime = datetime.strptime(genTime, "%Y-%m-%d %H:%M:%S")
    nowDateTime = datetime.utcnow()
    # Calculate time period between present and key generation
    diffSeconds = ((nowDateTime.hour * 60 + nowDateTime.minute) * 60 + nowDateTime.second) - ((generatedDateTime.hour * 60 + generatedDateTime.minute) * 60 + generatedDateTime.second)
    if (activated == 0 and diffSeconds < 86400):
        return True        
    return False 