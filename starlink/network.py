from flask import (
    Blueprint, flash, redirect, render_template, request, abort, url_for, current_app, g
)
import ipaddress, pycountry, socket, re, datetime
import pandas as pd

# App imports
from starlink.db import get_db

bp = Blueprint('network', __name__, url_prefix='/network')

# Dashboard for firmware page
@bp.route('/')
def index():
    db = get_db()
    cloudflareIp = request.headers.get('cf-connecting-ip')
    if cloudflareIp is None:
        cloudflareIp = "0.0.0.0"
    cloudflareIp = "2803:9810:4000:0000:0000:0000:0000:0000" #temp
    geoIp = pd.read_csv('https://geoip.starlinkisp.net/feed.csv', names=['subnet', 'country', 'state', 'city', 'NaN'], header=None)

    for index, row in geoIp.iterrows():       
        if ipaddress.ip_address(cloudflareIp) in ipaddress.ip_network(row['subnet']): 
            isp = "Starlink"
            try:
                pop = re.search("(?<=customer.)(.*)(?=.pop)", socket.gethostbyaddr(cloudflareIp)[0]).group()
            except Exception as e:
                pop = "N/A"
            
            country = pycountry.countries.get(alpha_2=row['country']).name
            city = row['city']
            checkDatabase(cloudflareIp, row['country'])
            break

        else:
            isp = "Not Starlink"
            pop = "N/A"
            country = "N/A"
            city = "N/A"
    
    userNetwork = {'ip': cloudflareIp, 'isp': isp, 'pop': pop, 'country': country, 'city': city}
    
    return render_template('network/index.html', userNetwork=userNetwork)

@bp.route('/mapbox')
def mapbox():
    db = get_db()
    countriesIpv4 = ""
    countriesIpv6 = ""

    countriesIpv4Db = db.execute('SELECT DISTINCT country FROM network WHERE protocol_type = ?', ("ipv4",))
    for country in countriesIpv4Db:
        countriesIpv4 += country[0] + ","
    countriesIpv4 = countriesIpv4[:-1]

    countriesIpv6Db = db.execute('SELECT DISTINCT country FROM network WHERE protocol_type = ?', ("ipv6",))
    for country in countriesIpv6Db:
        countriesIpv6 += country[0] + ","
    countriesIpv6 = countriesIpv6[:-1]

    mapboxKey = current_app.config['MAPBOX_KEY']

    return render_template('network/mapbox.html', mapboxKey=mapboxKey, countriesIpv4=countriesIpv4, countriesIpv6=countriesIpv6)


# Function to update db with most recent user IP
def checkDatabase(ip, country):
    db = get_db()
    # Determine protocol type
    ipProtocol = ipaddress.ip_address(ip)
    if ipProtocol.version == 4:
        protocolType = "ipv4"
    else:
        protocolType = "ipv6"

    dateNow = datetime.datetime.utcnow()
    
    # Check if IP already exists, if so update country code. Otherwise insert new entry
    dbCheck = db.execute('SELECT EXISTS (SELECT 1 FROM network WHERE ip = ? LIMIT 1)', (ip,)).fetchone()[0]
    if dbCheck == 1:
        db.execute('UPDATE network SET country = ?, date_seen = ? WHERE ip = ?', (country, dateNow, ip))
        db.commit()
    else:
        db.execute('INSERT INTO network (ip, protocol_type, country, date_seen) VALUES (?, ?, ?, ?)', (ip, protocolType, country, dateNow))
        db.commit()