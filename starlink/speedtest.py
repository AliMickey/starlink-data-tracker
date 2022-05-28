from flask import (
    Blueprint, render_template, request, flash
)
import re, schedule, requests, json, sqlite3
from datetime import datetime
from threading import Thread
from bs4 import BeautifulSoup
from time import sleep

# App imports
from starlink.db import get_db

bp = Blueprint('speedtest', __name__, url_prefix='/speedtests')

requestHeaders = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
    }

# View to show the index page of speedtest results
@bp.route('/', methods = ['GET', 'POST'])
def index():
    db = get_db()
    listDict = {}
    statDict = {}

    rowData = db.execute('''
        SELECT id, url, datetime(date_run), country, latency, download, upload
        FROM speedtests
        ORDER BY date_run
        DESC LIMIT 10
        ''').fetchall()

    for row in rowData:
        id, url, date_run, country, latency, download, upload = row
        convDate = datetime.strptime(date_run, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
        listDict[id] = {'url': url, 'dateRun': convDate, 'country': country, 'latency': latency, 'download': f'{download/1000:.1f}', 'upload': f'{upload/1000:.1f}'}
    schedCalcStats()
    for period in ['day', 'week', 'month', 'year', 'all']:
        data = db.execute('''
            SELECT count, latency_avg, latency_max, latency_min, download_avg, download_max, download_min, upload_avg, upload_max, upload_min
            FROM speedtest_stats
            WHERE period = ?
            ''', (period,)).fetchone()

        if data[0] > 0:
            latencyAvg = f'{data[1]:.0f}'
            latencyMax = f'{data[2]:.0f}'
            latencyMin = f'{data[3]:.0f}'
            downloadAvg = f'{data[4]/1000:.2f}'
            downloadMax = f'{data[5]/1000:.2f}'
            downloadMin = f'{data[6]/1000:.2f}'
            uploadAvg = f'{data[7]/1000:.2f}'
            uploadMax = f'{data[8]/1000:.2f}'
            uploadMin = f'{data[9]/1000:.2f}'
            
        else:
            latencyAvg = latencyMax = latencyMin = downloadAvg = downloadMax = downloadMin = uploadAvg = uploadMax = uploadMin = "No Data"

        statDict[period] = {'count': data[0], 'latencyAvg': latencyAvg, 'latencyMax': latencyMax, 'latencyMin': latencyMin, 'downloadAvg': downloadAvg, 
                            'downloadMax': downloadMax, 'downloadMin': downloadMin,  'uploadAvg': uploadAvg,  'uploadMax': uploadMax, 'uploadMin': uploadMin}
    
    return render_template('speedtest/index.html', listDict=listDict, statDict=statDict)
    

# View to show the all time leaderboard
@bp.route('/leaderboard', methods = ['GET'])
def leaderboard():
    db = get_db()
    statDict = {'latency': [], 'download': [], 'upload': []}
    
    latency = db.execute('''
        SELECT latency, url, country, date_run
        FROM speedtests
        ORDER BY latency asc LIMIT 3
        ''').fetchall()
    download = db.execute('''
        SELECT download, url, country, date_run
        FROM speedtests
        ORDER BY download DESC LIMIT 3
        ''').fetchall()
    upload = db.execute('''
        SELECT upload, url, country, date_run
        FROM speedtests
        ORDER BY upload DESC LIMIT 3
        ''').fetchall()

    for result in latency:
        index = latency.index(result)
        statDict['latency'].append({'latency': latency[index][0], 'url': latency[index][1], 'country': latency[index][2], 'date': datetime.strptime(latency[index][3], "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")})

    for result in download:
        index = download.index(result)
        statDict['download'].append({'download': f'{download[index][0]/1000:.2f}', 'url': download[index][1], 'country': download[index][2], 'date': datetime.strptime(download[index][3], "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")})

    for result in upload:
        index = upload.index(result)
        statDict['upload'].append({'upload': f'{upload[index][0]/1000:.2f}', 'url': upload[index][1], 'country': upload[index][2], 'date': datetime.strptime(upload[index][3], "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")})
        
    return render_template('speedtest/leaderboard.html', statDict=statDict)


# View & function to add new speedtests
@bp.route('/add', methods = ['GET', 'POST'])
def add():
    db = get_db()
    error = None

    if request.method == 'POST':
        url = request.form['url']
        if re.search('https://www.speedtest.net/result', url): # If url is valid
            if re.search('png', url): # If an image was picked up, get the id and convert to ordinary url
                    url = url.replace(".png", "")
            dbCheck = db.execute('SELECT EXISTS (SELECT 1 FROM speedtests WHERE url = ? LIMIT 1)', (url,)).fetchone()[0]
            if dbCheck == 0: # If speedtest result does not exist in db
                response = requests.get(url, timeout=5, headers=requestHeaders)
                page_html = BeautifulSoup(response.text, 'html.parser')
                scripts = list(filter(lambda script: not script.has_attr("src"), page_html.find_all("script")))
                for script in scripts:
                    if "window.OOKLA.INIT_DATA" in script.get_text():
                        result = re.search('({"result").*}}*', script.get_text())       
                        data = json.loads(result.group())['result']
                        if data['isp_name'] == "SpaceX Starlink": # If ISP is Starlink
                            if int(data['latency']) <= 5 or int(data['download']) >= 600000 or int(data['upload']) >= 50000: # If test results are not within a valid for Starlink
                                error = "Speedtest contains potentially inaccurate results. Contact Tech Support for help."
                            else:
                                db.execute('INSERT INTO speedtests (date_added, date_run, url, country, server, latency, download, upload) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                                    (datetime.utcnow(), datetime.utcfromtimestamp(data['date']), url, data['country_code'].lower(), data['sponsor_name'], int(data['latency']), int(data['download']), int(data['upload'])))
                                db.commit()
                        else:
                            error = "Speedtest was not run on Starlink."
                        break # Doesn't stop the for loop for some reason.
            else:
                error = "Speedtest result already exists."
        else:
            error = "URL must be in `https://www.speedtest.net/result/` format."

        if error is None:
            if request.form.get('bot'):
                return "Speedtest added successfully. Thanks!\nView it at https://starlinkversions.com/speedtests"     
            else:
                flash("Speedtest added successfully", "success")
        else:
            if request.form.get('bot'):
                return error
            else:
                flash(error, "danger")

    return render_template('speedtest/add.html')


# Function to calculate period stats while in thread
def schedCalcStats():
    dateNow = datetime.utcnow()
    datePastDay = dateNow.replace(day=dateNow.day - 1)
    datePastWeek = dateNow.replace(day=dateNow.day - 7)
    datePastMonth = dateNow.replace(month=dateNow.month - 1)
    datePastYear = dateNow.replace(year=dateNow.year - 1)
    dateAll = "1970-01-01"

    db = sqlite3.connect('instance/starlink.db')

    for period, value in {'day': datePastDay, 'week': datePastWeek, 'month': datePastMonth, 'year': datePastYear, 'all': dateAll}.items():
        latencyData = db.execute('''
            SELECT avg(latency), max(latency), min(latency)
            FROM speedtests
            WHERE date_run BETWEEN ? AND ?
            ''', (value, dateNow)).fetchone()
        downloadData = db.execute('''
            SELECT avg(download), max(download), min(download)
            FROM speedtests
            WHERE date_run BETWEEN ? AND ?
            ''', (value, dateNow)).fetchone()
        uploadData = db.execute('''
            SELECT avg(upload), max(upload), min(upload)
            FROM speedtests
            WHERE date_run BETWEEN ? AND ?
            ''', (value, dateNow)).fetchone()

        speedtestCount = db.execute('SELECT Count(id) FROM speedtests WHERE date_run BETWEEN ? AND ?', (value, dateNow)).fetchone()[0]

        db.execute('''
            UPDATE speedtest_stats SET count = ?, latency_avg = ?, latency_max = ?, latency_min = ?, download_avg = ?, download_max = ?, download_min = ?, 
            upload_avg = ?, upload_max = ?, upload_min = ? WHERE period = ?
            ''', (speedtestCount, latencyData[0], latencyData[1], latencyData[2], downloadData[0], downloadData[1], downloadData[2],
                    uploadData[0], uploadData[1], uploadData[2], period))
        db.commit()
    db.close()

# Function to start schedule thread
def schedInitJobs():
    schedule.every().second.do(schedCalcStats)
    thread = Thread(target=schedPendingRunner)
    thread.start()

# Function to keep scheduler running
def schedPendingRunner():
    while True:
        schedule.run_pending()
        sleep(10)