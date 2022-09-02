from flask import (
    Blueprint, current_app, render_template, request, flash, redirect, url_for, g
)
import re, requests, json, awoc, pycountry, pytz
import datetime
from bs4 import BeautifulSoup
import statistics

# App imports
from starlink.db import get_db

bp = Blueprint('speedtest', __name__, url_prefix='/speedtests')

requestHeaders = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
    }

speedtestPeriods = ['day', 'week', 'month', 'year', 'all']
continents = ['africa', 'antarctica', 'asia', 'europe', 'north_america', 'oceania', 'south_america']
regionData = awoc.AWOC()

# View to show the index page of speedtest results & stats
@bp.route('/', methods = ['GET'], defaults={'region': 'global'})
@bp.route('/region/<string:region>')
def index(region):
    db = get_db()
    error = None
    listDict = {}
    statDict = {}
    region = region.lower()
    periodSelect = request.args.get('period', default = 'day', type = str)
    mapboxKey = current_app.config['MAPBOX_KEY']
    regionBbox = json.load(open(current_app.root_path + '/static/other/regions-bbox.json'))[region]
    timezone = "UTC"
    if g.user:
        timezone = g.user['time_zone']

    # Recently added

    # Global
    if region == "global": # Get latest rows for every country
        regionName = region.capitalize() # Prettify region name
        countries = [d['ISO2'].lower() for d in regionData.get_countries()]

    # Continent
    elif region in continents:
        regionName = region.replace('_', ' ').title() # Prettify region name
        countries = [d['ISO2'].lower() for d in regionData.get_countries_data_of(regionName)]

    # Country
    else: # Get latest rows for specific country
        regionCheck = pycountry.countries.get(alpha_2=region)  
        if regionCheck:
            regionName = regionCheck.name
            countries = [region]
        
        else: # Return invalid region error
            flash("Supplied region code is incorrect.", "warning")
            return redirect(url_for('speedtest.index'))

    # Convert list into string for sqlite to parse correctly
    countries = "'" + "','".join(list(map(str, countries))) + "'"

    listDB = db.execute(f'''
            SELECT id, url, datetime(date_run), country, latency, download, upload
            FROM speedtests
            WHERE country in ({countries})
            ORDER BY date_run
            DESC LIMIT 10
            ''').fetchall()
    
    for row in listDB:
        id, url, date_run, country, latency, download, upload = row
        convDate = datetime.datetime.strptime(date_run, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
        listDict[id] = {'url': url, 'dateRun': convDate, 'country': country, 'latency': latency, 'download': f'{download / 1000:.1f}', 'upload': f'{upload / 1000:.1f}'}
    

    # Statistics
    data = {}
    todayDateTime = datetime.datetime.now(pytz.timezone(timezone))

    # Day
    currentPeriodStart = (todayDateTime - datetime.timedelta(days=1))
    regionDayStats = getStats(countries, currentPeriodStart, todayDateTime, "%H", [0, 24])
    
    # Shift hour codes relative to country timezone
    tempData = {}
    for hour, hourData in regionDayStats["aggregate"].items():
        utcDateTime = datetime.datetime(1970,1,1,int(hour),0,0)
        convDateTime = str(utcDateTime.replace(tzinfo=datetime.timezone.utc).astimezone(pytz.timezone(timezone)).hour)
        if len(convDateTime) == 1:
            convDateTime = "0" + convDateTime
        newHour = str(convDateTime)
        tempData[newHour] = hourData
        regionDayStats["aggregate"] = tempData

    # Week
    currentPeriodStart = todayDateTime - datetime.timedelta(days=7)
    regionWeekStats = getStats(countries, currentPeriodStart, todayDateTime, "%w", [0, 7])

    # Month
    currentPeriodStart = todayDateTime - datetime.timedelta(weeks=4)
    regionMonthStats = getStats(countries, currentPeriodStart, todayDateTime, "%d", [1, 32])

    # Year
    currentPeriodStart = todayDateTime - datetime.timedelta(weeks=52)
    regionYearStats = getStats(countries, currentPeriodStart, todayDateTime, "%m", [1, 13])

    # All
    currentPeriodStart = "1970-01-01"
    regionAllStats = getStats(countries, currentPeriodStart, todayDateTime, "%Y", [2020, 2023])

    statDict = {"day": regionDayStats, "week": regionWeekStats, "month": regionMonthStats, "year": regionYearStats, "all": regionAllStats}

    return render_template('speedtest/index.html', regionName=regionName, statDict=statDict, listDict=listDict, periodSelect=periodSelect, mapboxKey=mapboxKey, regionBbox=regionBbox)

# View to show speedtest results & stats for a user
# Under development
@bp.route('/user/<string:username>', methods = ['GET'])
def user(username):
    db = get_db()
    error = None
    listDict = {}

    userId = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if userId:
        listDB = db.execute('''
            SELECT id, url, datetime(date_run), country, latency, download, upload
            FROM speedtests
            WHERE user_id = ?
            ORDER BY date_run
            DESC LIMIT 10
            ''', (userId)).fetchall()

        for row in listDB:
            id, url, date_run, country, latency, download, upload = row
            convDate = datetime.datetime.strptime(date_run, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
            listDict[id] = {'url': url, 'dateRun': convDate, 'country': country, 'latency': latency, 'download': f'{download/1000:.1f}', 'upload': f'{upload/1000:.1f}'}
    
    else:
        flash("User not found", "warning")
        return redirect(url_for('speedtest.index'))

    return render_template('speedtest/user.html', username=username, listDict=listDict)

# View to show the all time leaderboard
@bp.route('/leaderboard', methods = ['GET'])
def leaderboard():
    db = get_db()
    error = None
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
        statDict['latency'].append({'latency': latency[index][0], 'url': latency[index][1], 'country': latency[index][2], 'date': datetime.datetime.strptime(latency[index][3], "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")})

    for result in download:
        index = download.index(result)
        statDict['download'].append({'download': f'{download[index][0]/1000:.2f}', 'url': download[index][1], 'country': download[index][2], 'date': datetime.datetime.strptime(download[index][3], "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")})

    for result in upload:
        index = upload.index(result)
        statDict['upload'].append({'upload': f'{upload[index][0]/1000:.2f}', 'url': upload[index][1], 'country': upload[index][2], 'date': datetime.datetime.strptime(upload[index][3], "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")})
        
    return render_template('speedtest/leaderboard.html', statDict=statDict)

# View & function to add new speedtests
@bp.route('/add', methods = ['GET', 'POST'])
def add():
    db = get_db()
    error = None
    source = ""

    if request.method == 'POST':
        url = request.form['url']
        apiKey = request.form.get('api-key')
        if apiKey:
            apiDetails = db.execute('SELECT user_id, source, use_counter FROM users_api_keys WHERE key = ?', (apiKey,)).fetchone()
            if apiDetails: # If the supplied api key is valid
                userId = apiDetails['user_id']
                source = apiDetails['source']
                if source == 'discord-starlink': # If form was submitted by discord bot, lookup user id for discord id.
                    discordUserId = request.form['discord-user-id']
                    userIdCheck = db.execute('SELECT id FROM users WHERE discord_id = ?', (discordUserId,)).fetchone()
                    if userIdCheck: # Set user id if user has set a discord id in account settings
                        userId = int(userIdCheck['id'])

                db.execute('UPDATE users_api_keys SET use_counter = ? WHERE key = ?', (apiDetails['use_counter'] + 1, apiKey))
                db.commit()
            else:
                error = "API key is not valid"
        else:
            if g.user: # Authenticated user on website
                userId = g.user['id']
                source = "website-official"
            else: # Either website form or external POST (source is classified as website as external POST without an API key is rare)
                userId = None
                source = "website-official"

        # Convert into clean url
        if re.search('png', url): # If an image was picked up, get the id and convert to ordinary url
                    url = url.replace(".png", "")
        if re.search('my-result', url):
                    url = url.replace("my-result", "result")

        # Continue if url is valid with base domain
        if re.search('^https://www.speedtest.net/result/.\S*$', url):
            dbCheck = db.execute('SELECT EXISTS (SELECT 1 FROM speedtests WHERE url = ? LIMIT 1)', (url,)).fetchone()[0]
            if dbCheck == 0: # If speedtest result does not exist in db
                try:
                    response = requests.get(url, timeout=5, headers=requestHeaders)
                    page_html = BeautifulSoup(response.text, 'html.parser')
                    scripts = list(filter(lambda script: not script.has_attr("src"), page_html.find_all("script")))[::-1] # Reverse list to improve speed because data script is at the end of <head>
                    dataScript = None
                    for script in scripts:
                        if "window.OOKLA.INIT_DATA" in script.get_text():
                            dataScript = script
                            break
                    if dataScript:
                        result = re.search('({"result").*}}*', dataScript.get_text())       
                        data = json.loads(result.group())['result']
                        if data['isp_name'] == "SpaceX Starlink": # If ISP is Starlink
                            if int(data['distance']) >= 500: # If test conducted has a distance greater than 500 miles between server and Starlink POP
                                error = "The speedtest was measured with a server that is far away from your location. This can lead to inaccurate results. Please ensure you select a server that is close to you."
                            elif int(data['latency']) <= 5 or int(data['download']) >= 600000 or int(data['download']) <= 500 or int(data['upload']) >= 55000 or int(data['upload']) <= 500: # If test results are not within a valid range (<5ms latency, 1-600mbps download, 0.5-50mbps upload) for Starlink (may change in the future)
                                error = "Speedtest contains potentially inaccurate results. Please try again.\nLimits: Latency (> 5ms), Download (600mbps - 0.5mbps), Upload(55mbps - 0.5mbps)."
                            else: # Add speedtest                                 
                                db.execute('INSERT INTO speedtests (date_added, date_run, url, country, server, latency, download, upload, source, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                                    (datetime.datetime.utcnow(), datetime.datetime.utcfromtimestamp(data['date']), url, data['country_code'].lower(), data['server_name'], int(data['latency']), int(data['download']), int(data['upload']), source, userId))
                                db.commit()
                        else:
                            error = "Speedtest was not run on Starlink."
                    else:
                        error = "Speedtest result could not be found. Ensure the URL is correct."
                except Exception as e:
                    error = "Speedtest could not be added. Please tag Tech Support."
                    print(e)
            else:
                error = "Speedtest result already exists."
        else:
            error = "URL must be in `https://www.speedtest.net/result/` format as a standalone message."

        if error is None:
            if source == "website-official":
                flash("Speedtest added successfully.", "success")
            else:
                return "Speedtest added successfully, thanks!"     
        else:
            if source == "website-official":
                flash(error, "warning")
            else:
                return error

    return render_template('speedtest/add.html')

# Function to calculate stats for provided region and period type
def getStats(countries, currentPeriodStart, dateTimeNow, strftimeCode, aggregateRange):
    db = get_db()
    data = {'current': {}, 'aggregate': {}}

    data["current"] = dict(db.execute(f'''SELECT count(id) as count,
        round(avg(latency), 0) as latency_avg,
        round(min(latency), 0) as latency_min,
        round(max(latency), 0) as latency_max,
        group_concat(latency, ",") as latency_sd,
        round(avg(download) / 1000, 0) as download_avg,
        round(min(download) / 1000, 0) as download_min,
        round(max(download) / 1000, 0) as download_max,
        group_concat(download / 1000, ",") as download_sd,
        round(avg(upload) / 1000, 0) as upload_avg,
        round(min(upload) / 1000, 0) as upload_min,
        round(max(upload) / 1000, 0) as upload_max,
        group_concat(upload / 1000, ",") as upload_sd
        FROM speedtests WHERE date(date_run) BETWEEN ? AND ?
        AND country in ({countries})
    ''', (currentPeriodStart, dateTimeNow)).fetchone())
    
    if data["current"]["count"] <= 1:
        # Rename None to No Data
        data["current"] = {x: "N/A" for x in data["current"]}
        data["current"]["count"] = 0
            
    else:
        # Calculate standard deviation using returned group_concat string
        for metric in ["latency", "download", "upload"]: 
            data["current"][metric + "_sd"] = round(statistics.stdev([int(s) for s in data["current"][metric + "_sd"].split(',')]))
 
    # Get aggregate stats for all sub period ranges
    for rangeItem in range(aggregateRange[0], aggregateRange[1]):
        rangeItem = str(rangeItem)
        if len(rangeItem) == 1 and strftimeCode != '%w': # Special edge case for week days, single digits required
            rangeItem = "0" + rangeItem

        tempData = db.execute(f'''SELECT count(id) as count,
            round(avg(latency), 0) as latency_avg,
            round(min(latency), 0) as latency_min,
            round(max(latency), 0) as latency_max,
            round(avg(download) / 1000, 2) as download_avg,
            round(min(download) / 1000, 2) as download_min,
            round(max(download) / 1000, 2) as download_max,
            round(avg(upload) / 1000, 2) as upload_avg,
            round(min(upload) / 1000, 2) as upload_min,
            round(max(upload) / 1000, 2) as upload_max
            FROM speedtests WHERE strftime("{strftimeCode}", date_run) = ?
            AND country in ({countries})
        ''', (rangeItem,)).fetchone()
        data['aggregate'][rangeItem] = dict(tempData)

    return data