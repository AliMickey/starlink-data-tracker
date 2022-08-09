from flask import (
    Blueprint, current_app, g, redirect, render_template, request, session, url_for, flash
)
from werkzeug.security import check_password_hash, generate_password_hash
import functools, re, uuid, requests, pytz
from datetime import datetime, timedelta
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
        hcaptchaSecret = current_app.config['HCAPTCHA_KEY']
        hcaptchaResponse = requests.post(url = "https://hcaptcha.com/siteverify", data = {'secret': hcaptchaSecret, 'response': captcha}).json()
        
        if not hcaptchaResponse['success']:
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
        elif len(username) >= 10:
            error = "Username must be a maximum of 10 characters"
        elif predict([username]) == 1:
            error = "Username contains profanity"
        elif not password or not passwordRepeat:
            error = "Password is required"
        elif len(password) < 8:
            error = "Password must be a minimum of 8 characters"
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
@login_required
def account():
    error = None
    db = get_db()
    userDetails = db.execute('SELECT id, email, username, time_zone, discord_id FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    userApiKeys = db.execute('SELECT key, name, use_counter FROM users_api_keys WHERE user_id = ?', (g.user['id'],)).fetchall()
    timezones = pytz.common_timezones

    if request.method == 'POST':
        if request.form["btn"] == "user": # General user account settings
            username = request.form['username']
            timezone = request.form['timezone']
            userUsernameCheck =  db.execute('SELECT EXISTS (SELECT 1 FROM users WHERE username = ? LIMIT 1)', (username,)).fetchone()[0]

            # Check if submitted username is different and unique
            if username != userDetails['username']:
                if userUsernameCheck == 1:
                    error = "Username is taken"
            # Check if submitted timezone is a valid format
            elif timezone not in pytz.all_timezones_set:
                error = "Invalid time zone provided"

            if error is None:
                db.execute('UPDATE users SET username = ?, time_zone = ? WHERE id = ?', (username, timezone, g.user['id']))
                db.commit()

        elif request.form["btn"] == "delete-user": # Delete user account
            userId = g.user['id']
            db.execute('DELETE FROM users WHERE id = ?', (userId,))
            db.execute('DELETE FROM users_api_keys WHERE user_id = ?', (userId,))
            db.execute('DELETE FROM users_password_reset WHERE user_id = ?', (userId,))
            db.commit()

        elif request.form["btn"] == "api-key-new": # Add a new api key for user
            apiKeyName = request.form['apiKeyNewName']

            if len(userApiKeys) == 3:
                error = "API Key limit reached"
            elif not apiKeyName:
                error = "An API key name is required"
            
            if error is None:
                apiKey = str(uuid.uuid1())
                db.execute('INSERT INTO users_api_keys (key, date_time, source, name, use_counter, user_id) VALUES (?, ?, ?, ?, ?, ?)', 
                        (apiKey, datetime.utcnow(), 'script-official', apiKeyName, 0, g.user['id']))
                db.commit()

        elif request.form["btn"] == "api-key-delete": # Delete specified api key for user
            apiKey = request.form['apiKey']
            for key in userApiKeys: # Validation to check if specified api key is owned by user
                if apiKey == key['key']:
                    db.execute('DELETE FROM users_api_keys WHERE key = ?', (apiKey,))
                    db.commit()
                    break

        elif request.form["btn"] == "speedtest": # Speedtest related account settings
            discordId = request.form['discordId']

            if error is None:
                db.execute('UPDATE users SET discord_id = ? WHERE id = ?', (discordId, g.user['id']))
                db.commit()

        if error:
            flash(error, "warning")
        return redirect(url_for('auth.account'))

    return render_template('auth/account.html', userDetails=userDetails, userApiKeys=userApiKeys, timezones=timezones)

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
            # Allow only two password reset requests per day
            datePastDay = datetime.utcnow() - timedelta(days=1)
            resetPassCount = db.execute('SELECT count(id) FROM users_password_reset WHERE user_id = ? AND date_time BETWEEN ? AND ?', (userID, datePastDay, datetime.utcnow())).fetchone()            
            if resetPassCount[0] < 2:
                # Generate and send a new key
                resetKey = uuid.uuid4()
                db.execute('INSERT INTO users_password_reset (reset_key, user_id, date_time, activated) VALUES (?, ?, ?, ?) ', 
                    (str(resetKey), userID, datetime.utcnow(), False))
                db.commit()

                sendEmail(email, "Reset password", f"Use the following link to reset your password for Starlink Data Tracker. https://starlinktrack.com/auth/reset-password/{resetKey}")
        
        # Generic message to prevent brute email validity checks
        error = "If the provided email exists, you will soon receive an email with instructions. Please check your spam folder. (You can only change your password twice per day)"
        
        if error:
            flash(error, "success")

    return render_template('auth/forgot-password.html')

# View to reset password via uuid
@bp.route('/reset-password/<string:resetKey>', methods=('GET', 'POST'))
def resetPassword(resetKey):
    error = None
    db = get_db()          
    resetPassDetails = db.execute('SELECT user_id, datetime(date_time), activated FROM users_password_reset WHERE reset_key = ?', (resetKey,)).fetchone()
    
    # Check if url key is valid upon initial load
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

# Function to check if account verify key is still valid       
def checkAccountActivationKeyValidity(userId):
    db = get_db()
    activationStatus = db.execute('SELECT activated FROM users WHERE id = ?', (userId,)).fetchone()
    print(activationStatus)
    if activationStatus:
        return True
    return False 