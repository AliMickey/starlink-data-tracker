from flask import (
    Blueprint, current_app, render_template, request, flash, redirect, url_for, g
)
import re, requests, json, pycountry, pytz, datetime, statistics
from time import sleep
from bs4 import BeautifulSoup

# App imports
from app.functions.wrappers import exception_handler
from app.functions.db import get_db

bp = Blueprint('speedtest', __name__, url_prefix='/speedtests')

# View to show the index page of speedtest results & stats
@bp.route('/', methods = ['GET', 'POST'], defaults={'region': 'global'})
@bp.route('/region/<string:region>', methods = ['GET', 'POST'])
@exception_handler
def index(region):
    db = get_db()
    error = None
    region = region.replace(' ', '_').lower()
    listDict = {}
    statDict = {}
    continents = ['africa', 'antarctica', 'asia', 'europe', 'north_america', 'oceania', 'south_america']

    if request.method == 'POST':
        period = request.form['period']
        timezone = request.form.get('timezone')
        return redirect(url_for('speedtest.index', region=region, period=period, timezone=timezone))
        
    # Recently added
    # Global
    if region == "global": # Get latest rows for every country
        regionName = region.capitalize() # Prettify region name
        countries = [c.alpha_2.lower() for c in pycountry.countries]
        timezones = pytz.common_timezones
        timezone = "UTC"
        
    # Continent
    elif region in continents:
        regionName = region.replace('_', ' ').title() # Prettify region name

        continent_countries = {
            'africa': ['DZ', 'AO', 'BJ', 'BW', 'BF', 'BI', 'CM', 'CV', 'CF', 'TD', 'KM', 'CG', 'CD', 'CI', 'DJ', 'EG', 'GQ', 'ER', 'SZ', 'ET', 'GA', 'GM', 'GH', 'GN', 'GW', 'KE', 'LS', 'LR', 'LY', 'MG', 'MW', 'ML', 'MR', 'MU', 'MA', 'MZ', 'NA', 'NE', 'NG', 'RW', 'ST', 'SN', 'SC', 'SL', 'SO', 'ZA', 'SS', 'SD', 'TZ', 'TG', 'TN', 'UG', 'EH', 'ZM', 'ZW'],
            'antarctica': ['AQ'],
            'asia': ['AF', 'AM', 'AZ', 'BH', 'BD', 'BT', 'BN', 'KH', 'CN', 'CY', 'GE', 'IN', 'ID', 'IR', 'IQ', 'IL', 'JP', 'JO', 'KZ', 'KW', 'KG', 'LA', 'LB', 'MY', 'MV', 'MN', 'MM', 'NP', 'KP', 'OM', 'PK', 'PH', 'QA', 'SA', 'SG', 'KR', 'LK', 'SY', 'TJ', 'TH', 'TL', 'TR', 'TM', 'AE', 'UZ', 'VN', 'YE'],
            'europe': ['AL', 'AD', 'AM', 'AT', 'AZ', 'BY', 'BE', 'BA', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'GE', 'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'KZ', 'XK', 'LV', 'LI', 'LT', 'LU', 'MT', 'MD', 'MC', 'ME', 'NL', 'MK', 'NO', 'PL', 'PT', 'RO', 'RU', 'SM', 'RS', 'SK', 'SI', 'ES', 'SE', 'CH', 'UA', 'GB', 'VA'],
            'north_america': ['AG', 'BS', 'BB', 'BZ', 'CA', 'CR', 'CU', 'DM', 'DO', 'SV', 'GD', 'GT', 'HT', 'HN', 'JM', 'MX', 'NI', 'PA', 'KN', 'LC', 'VC', 'TT', 'US'],
            'oceania': ['AS', 'AU', 'CK', 'FJ', 'PF', 'GU', 'KI', 'MH', 'FM', 'NR', 'NC', 'NZ', 'NU', 'NF', 'MP', 'PW', 'PG', 'WS', 'SB', 'TK', 'TO', 'TV', 'VU', 'WF'],
            'south_america': ['AR', 'BO', 'BR', 'CL', 'CO', 'EC', 'GY', 'PY', 'PE', 'SR', 'UY', 'VE']
        }

        countries = [country.lower() for country in continent_countries[region]]
        timezones = []
        pytzValidCountries = list(pytz.country_names)
        for country in countries:
            if country.upper() in pytzValidCountries:
                countryTimezones = pytz.country_timezones[country]
                for tz in countryTimezones:
                    timezones.append(tz)
        timezone = timezones[0]
        
    # Special region for all countries except U.S.A.
    elif region == "rest-of-world":
        regionName = "Rest of World (Excluding U.S.A.)" # Prettify region name
        countries = [c.alpha_2.lower() for c in pycountry.countries]
        countries.remove("us")
        timezones = pytz.common_timezones
        timezone = "UTC"

    # Country
    else: # Get latest rows for specific country
        regionCheck = pycountry.countries.get(alpha_2=region)
        if regionCheck:
            regionName = regionCheck.name
            countries = [region]
            timezones = pytz.country_timezones[region]
            timezone = timezones[0]

        else: # Return invalid region error
            flash("Supplied region code is incorrect.", "warning")
            return redirect(url_for('speedtest.index'))

    period = request.args.get('period', default = 'year', type = str)
    timezone = request.args.get('timezone', default = 'UTC', type = str)
    filters = {'period': period, 'timezone': timezone}

    # Convert list into string for sqlite to parse correctly
    countries = "'" + "','".join(list(map(str, countries))) + "'"
    listDb = db.execute(f'''
            SELECT id, url, datetime(date_run), country, latency, download, upload
            FROM speedtests
            WHERE country in ({countries})
            ORDER BY date_run
            DESC LIMIT 10
            ''').fetchall()
    
    for row in listDb:
        id, url, date_run, country, latency, download, upload = row
        listDict[id] = {'url': url, 'dateRun': date_run, 'country': country, 'latency': latency, 'download': f'{download / 1000:.1f}', 'upload': f'{upload / 1000:.1f}'}
    
    # Statistics
    todayDateTime = datetime.datetime.now(datetime.UTC)

    if period == "day":
        # Day
        periodStart = datetime.datetime(todayDateTime.year, todayDateTime.month, todayDateTime.day)
        periodEnd = datetime.datetime(todayDateTime.year, todayDateTime.month, todayDateTime.day, 23, 59, 59)
        statDict['current'], statsAggregate = getStats(countries, periodStart, periodEnd, "%H", [0, 24])
        statDict['labels'] = "12AM,1AM,2AM,3AM,4AM,5AM,6AM,7AM,8AM,9AM,10AM,11AM,12PM,1PM,2PM,3PM,4PM,5PM,6PM,7PM,8PM,9PM,10PM,11PM"

        # Shift hour codes relative to country timezone
        tempData = {}
        for hour, hourData in statsAggregate.items():
            utcDateTime = datetime.datetime(1970,1,1,int(hour),0,0)
            convDateTime = str(utcDateTime.replace(tzinfo=datetime.timezone.utc).astimezone(pytz.timezone(timezone)).hour)

            if len(convDateTime) == 1: convDateTime = "0" + convDateTime
            newHour = str(convDateTime)
            tempData[newHour] = hourData
            statsAggregate = tempData
        statsAggregate = dict(sorted(statsAggregate.items()))

    elif period == "week":
        # Week
        periodStart = datetime.datetime.strptime(f'{todayDateTime.year}-W{todayDateTime.isocalendar()[1]}' + '-1', '%Y-W%W-%w') # Get first day of week from week number
        periodEnd = periodStart + datetime.timedelta(days=6,hours=23, minutes=59, seconds=59) # Add on 6 days to get end of week
        statDict['current'], statsAggregate = getStats(countries, periodStart, periodEnd, "%w", [0, 7])
        statDict['labels'] = "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday"

    elif period == "month":
        # Month
        periodStart = datetime.datetime(todayDateTime.year, todayDateTime.month, 1)  # Get first day of month
        periodEnd = datetime.datetime(todayDateTime.year + int(todayDateTime.month / 12), ((todayDateTime.month % 12) + 1), 1) # Get end of month (next month 00:00:00)
        statDict['current'], statsAggregate = getStats(countries, periodStart, periodEnd, "%d", [1, 32])
        statDict['labels'] = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"

    elif period == "year":
        # Year
        periodStart = datetime.datetime(todayDateTime.year, 1, 1) # Get first day of year
        periodEnd = datetime.datetime(todayDateTime.year, 12, 31, 23, 59, 59) # Set to 31 December for last day of year
        statDict['current'], statsAggregate = getStats(countries, periodStart, periodEnd, "%m", [1, 13])
        statDict['labels'] = "January,February,March,April,May,June,July,August,September,October,November,December"

    elif period == "all":
        # All
        periodStart = "2019-01-01" # Day before any speedtests were collected
        periodEnd = todayDateTime # Get last day as today
        statDict['current'], statsAggregate = getStats(countries, periodStart, periodEnd, "%Y", [2021, 2026])
        statDict['labels'] = "2021,2022,2023,2024,2025"

    latencyData = ""
    downloadData = ""
    uploadData = ""
    for index, stat in statsAggregate.items():
        latencyData += str(stat['latency_avg']) + ","
        downloadData += str(stat['download_avg']) + ","
        uploadData += str(stat['upload_avg']) + ","
    statDict['latency'] = latencyData[:-1]
    statDict['download'] = downloadData[:-1]
    statDict['upload'] = uploadData[:-1]

    regionBbox = json.load(open(current_app.root_path + '/static/other/regions-bbox.json'))[region]
    mapboxKey = current_app.config['MAPBOX_KEY']

    return render_template('speedtest/index.html', regionName=regionName, regionCode=region, timezones=timezones, statDict=statDict, listDict=listDict, filters=filters, mapboxKey=mapboxKey, regionBbox=regionBbox)

# View to show speedtest results & stats for a user
@bp.route('/user/<string:username>', methods = ['GET'])
@exception_handler
def user(username):
    db = get_db()
    error = None
    listDict = {}

    userId = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if userId:
        listDb = db.execute('''
            SELECT id, url, datetime(date_run), country, latency, download, upload
            FROM speedtests
            WHERE user_id = ?
            ''', (userId[0],)).fetchall()

        for row in listDb:
            id, url, date_run, country, latency, download, upload = row
            listDict[id] = {'url': url, 'dateRun': date_run, 'country': country, 'latency': latency, 'download': f'{download / 1000:.1f}', 'upload': f'{upload / 1000:.1f}'}
    
        statDict = dict(db.execute(f'''SELECT count(id) as count,
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
            FROM speedtests WHERE user_id = ?
        ''', (userId)).fetchone())

        if statDict["count"] == 0:
            # Rename None to No Data
            statDict = {x: "N/A" for x in statDict}

        elif statDict["count"] == 1:
            # Set SD to N/A since more than one data point is needed
            for metric in ["latency", "download", "upload"]: 
                statDict[metric + "_sd"] = "N/A"
        
        else:
            # Calculate standard deviation using returned group_concat string
            for metric in ["latency", "download", "upload"]: 
                statDict[metric + "_sd"] = round(statistics.stdev([int(s) for s in statDict[metric + "_sd"].split(',')]))

    else:
        flash("User not found", "warning")
        return redirect(url_for('speedtest.index'))

    return render_template('speedtest/user.html', username=username, listDict=listDict, statDict=statDict)

# View to show the all time leaderboard
@bp.route('/leaderboard', methods = ['GET'])
@exception_handler
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
@exception_handler
def add():
    db = get_db()
    error = None
    source = ""

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            urls = data.get('speedtest_url') 
        else:
            urls = request.form['urls']

        if request.args.get('api-key'):
            apiKey = request.args.get('api-key')
        elif request.form.get('api-key'):
            apiKey = request.form.get('api-key')
        else:
            apiKey = None            

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
        
        # Find all valid speedtest result and split into array
        urlPattern = re.compile(r'https:\/\/www\.speedtest\.net\/(?:result|i|my-result|[a-z])\/(?:[a-z]\/)?[0-9a-zA-Z\-]+(?:\.png)?')
        urls = urlPattern.findall(urls)

        sleepTime = 0
        if len(urls) > 5:
            sleepTime = 2

        for url in urls:
            # Convert into clean url
            if re.search('png', url): # If an image was picked up, get the id and convert to ordinary url
                        url = url.replace(".png", "")
            if re.search('my-result', url):
                        url = url.replace("my-result", "result")

            dbCheck = db.execute('SELECT EXISTS (SELECT 1 FROM speedtests WHERE url = ? LIMIT 1)', (url,)).fetchone()[0]
            if dbCheck == 0: # If speedtest result does not exist in db
                response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'})
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
                    country_code = None

                    if data['isp_name'] == "SpaceX Starlink": # If ISP is Starlink
                        
                        # Alternative method to check country code after Ookla stopped providing country_code in early 2025.
                        city_mapping = json.loads(open(current_app.root_path + '/static/other/city-mapping.json').read())
                        
                        server_name = data['server_name']
                        server_name_split = server_name.split(",")[0].lower()

                        if server_name_split in city_mapping:
                            country_code = city_mapping[server_name_split]

                        if country_code is None:
                            error = f"Could not detect country from {server_name}, ping a moderator."
                        elif int(data['latency']) <= 5 or int(data['download']) >= 600000 or int(data['download']) <= 500 or int(data['upload']) >= 65000 or int(data['upload']) <= 500: # If test results are not within a valid range (<5ms latency, 1-600mbps download, 0.5-50mbps upload) for Starlink (may change in the future)
                            error = "Speedtest contains potentially inaccurate results. Please try again.\nLimits: Latency (> 5ms), Download (600mbps - 0.5mbps), Upload(60mbps - 0.5mbps)."
                        else: # Add speedtest             
                            db.execute('INSERT INTO speedtests (date_added, date_run, url, country, server, latency, download, upload, source, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                                (datetime.datetime.now(datetime.UTC), datetime.datetime.fromtimestamp(data['date'], tz=datetime.timezone.utc), url, country_code, server_name, int(data['latency']), int(data['download']), int(data['upload']), source, userId))
                            db.commit()
                    else:
                        error = "Speedtest was not run on Starlink."
                else:
                    error = "Speedtest result could not be found. Ensure the URL is correct."
            else:
                error = "Speedtest result already exists."

            sleep(sleepTime) # Sleep to not get rate limited

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
@exception_handler
def getStats(countries, periodStart, periodEnd, strftimeCode, aggregateRange):
    db = get_db()
    current = {}
    aggregate = {}

    current = dict(db.execute(f'''SELECT count(id) as count,
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
        FROM speedtests WHERE date_run BETWEEN ? AND ?
        AND country in ({countries})
    ''', (periodStart, periodEnd)).fetchone())
    
    if current["count"] == 0:
        # Rename None to No Data
        current = {x: "N/A" for x in current}

    elif current["count"] == 1:
        # Set SD to N/A since more than one data point is needed
        for metric in ["latency", "download", "upload"]: 
            current[metric + "_sd"] = "N/A"
    
    else:
        # Calculate standard deviation using returned group_concat string
        for metric in ["latency", "download", "upload"]: 
            current[metric + "_sd"] = round(statistics.stdev([int(s) for s in current[metric + "_sd"].split(',')]))
 
    # Get aggregate stats for all sub period ranges
    for rangeItem in range(aggregateRange[0], aggregateRange[1]):
        rangeItem = str(rangeItem)
        if len(rangeItem) == 1 and strftimeCode != '%w': # Special edge case for week days, single digits required
            rangeItem = "0" + rangeItem

        tempData = db.execute(f'''SELECT count(id) as count,
            round(avg(latency), 0) as latency_avg,
            round(avg(download) / 1000, 2) as download_avg,
            round(avg(upload) / 1000, 2) as upload_avg
            FROM speedtests WHERE strftime("{strftimeCode}", date_run) = ?
            AND country in ({countries})
        ''', (rangeItem,)).fetchone()
        aggregate[rangeItem] = dict(tempData)

    return current, aggregate
