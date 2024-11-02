from flask import (
    Blueprint, flash, redirect, render_template, request, abort, url_for, current_app, g
)
from discord_webhook import DiscordWebhook, DiscordEmbed
import re, datetime

# App imports
from app.functions.db import get_db
from app.views.auth import login_required

bp = Blueprint('firmware', __name__, url_prefix='/firmware')

# Dashboard for firmware page
@bp.route('/')
def index():
    # Get firmware data for the past 5 dishy entries
    dishyListDict = getFirmwareData(listType="dishy", range=5)
    routerListDict = getFirmwareData(listType="router", range=4)
    appListDict = getFirmwareData(listType="app", range=4)

    return render_template('firmware/index.html', dishyListDict=dishyListDict, routerListDict=routerListDict, appListDict=appListDict)

# View to show all firmware versions for a specific hardware/software type
@bp.route('/<string:listType>', methods = ['GET', 'POST'])
def list(listType):
    if request.method == 'POST':
        db = get_db()
        if request.form["btn"] == "addRedditThread":
            redditThread = request.form['redditThread']
            versionID = request.form['id']
            p = re.compile("https://www.reddit.com/r/Starlink|https://reddit.com/r/Starlink")
            if re.search(p, redditThread):
                db.execute('UPDATE firmware SET reddit_thread = ? WHERE id = ?', (redditThread, versionID))
                db.commit()
                flash("Reddit Thread updated successfully", "success")
            else:
                flash("Reddit link must be valid. (Only from r/Starlink)", "warning")
            return redirect(request.referrer)

    if listType in ['dishy', 'router', 'app', 'web', 'hardware']: # Return the view only if listType is valid
        listDict = getFirmwareData(listType)
        return render_template('firmware/list.html', listType=listType, listDict=listDict)

    else:
        abort(404)

# View for admins to view/edit/delete data
@bp.route('/<string:listType>/admin', methods = ['GET', 'POST'])
@login_required
def listAdmin(listType):
    db = get_db()  
    if g.user['role'] == "admin":
        if request.method == 'POST':
            # Update version entry in db
            if request.form["btn"] == "updateVersion":
                versionID = request.form['versionID']
                dateTimeAdded = request.form['dateTimeAdded']
                version = request.form['version']
                redditThread = request.form['redditThread']

                db.execute('UPDATE firmware SET date_added = ?, version_info = ?, reddit_thread = ? WHERE id = ?', (dateTimeAdded, version, redditThread, versionID))
                db.commit()
                flash("Version updated successfully", "success")
                return redirect(request.referrer)

            # Remove existing version entry from db
            if request.form["btn"] == "removeVersion":
                versionID = request.form['versionID']
                db.execute('DELETE FROM firmware WHERE id = ?', (versionID,))
                db.commit()
                flash("Version removed successfully", "success")
                return redirect(request.referrer)   

        listDict = getFirmwareData(listType)
        return render_template('firmware/listAdmin.html', listType=listType, listDict=listDict)

    else:
        flash("Admin privileges required", "warning")
        return redirect(url_for('firmware.index'))

# View to add a new firmware version
@bp.route('/add', methods = ['GET', 'POST'])
def add():
    db = get_db()
    error = None

    if request.method == 'POST':
        listDetails = {'dishy': '^\d{4}[.]\d{2}[.]\d{2}[.](.{1,10})$',
                        'router': '^(\d{4}[.]\d{2}[.]\d{1,2}[.](mr)\d+)$', 
                        'app': '^\d{4}[.]\d{2}[.]\d{1}$',
                        'web': '^\d{1}[.]\d{1}[.]\d{1,2}$',
                        'hardware': ''}

        listType = request.form['listType']
        version = request.form['version']
        redditThread = request.form['redditThread']

        # Validation checks
        if listType in listDetails:
            dbCheck = db.execute('SELECT EXISTS (SELECT 1 FROM firmware WHERE type = ? AND version_info = ? LIMIT 1)', (listType, version)).fetchone()[0]
            listRegex = re.compile(listDetails[listType])
            if dbCheck == 1:
                error = "This version already exists"

            elif not re.search(listRegex, version):
                error = "Version format is not correct, refer to existing entries for the correct format"
            
            elif redditThread:
                redditURI = re.compile("https://www.reddit.com/r/Starlink|https://reddit.com/r/Starlink")
                if not re.search(redditURI, redditThread):
                    error = "Reddit link must be valid. (Only from r/Starlink)"
        else:
            error = "Invalid list type"

        if error is None:
            db.execute('INSERT INTO firmware (date_added, type, version_info, reddit_thread) VALUES (?, ?, ?, ?)', (datetime.datetime.now(datetime.UTC), listType, version, redditThread))
            db.commit()
            sendNotification(version, listType)
            return redirect(url_for('firmware.list', listType=listType))

        else:
            flash(error, "warning")
            return redirect(url_for('firmware.add'))
            
    return render_template('firmware/add.html')


# Function to get db data for firmware type
def getFirmwareData(listType, range=-1):
    db = get_db()
    listDict = {}
    rowData = db.execute('''
        SELECT id, datetime(date_added), version_info, reddit_thread
        FROM firmware
        WHERE type = ?
        ORDER BY date_added
        DESC LIMIT ?
    ''', (listType, range)).fetchall()

    for row in rowData:
        id, date_added, version, reddit = row
        convDate = datetime.datetime.strptime(date_added, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
        listDict[id] = {'dateAdded': convDate, 'dateTimeAdded': date_added, 'id': id, 'version': version, 'reddit': reddit}

    return listDict

# Function to send a notification to Starlink Discord channel
def sendNotification(version, type):
    webhook = DiscordWebhook(url=current_app.config['DISCORD_WEBHOOK'])
    hostDomain = url_for('index', _external=True)
    embed = DiscordEmbed(title=version, description=f"[starlinktrack.com]({hostDomain}firmware/{type})", color=242424)
    embed.add_embed_field(name='Firmware Type', value=type.capitalize())
    embed.set_thumbnail(url=hostDomain[:-1] + url_for('static', filename=f'img/firmware/thumbnails/{type}.png'))
    embed.set_timestamp()
    webhook.add_embed(embed)
    response = webhook.execute()
