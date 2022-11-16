from flask import (
    Blueprint, flash, redirect, render_template, request, abort, url_for, current_app, g
)
import ipaddress, pycountry, socket, re
import pandas as pd

# App imports
from starlink.db import get_db

bp = Blueprint('network', __name__, url_prefix='/network')

# Dashboard for firmware page
@bp.route('/')
def index():
    cloudflareIp = request.headers.get('cf-connecting-ip')
    if cloudflareIp is None:
        cloudflareIp = "0.0.0.0"
    geoIp = pd.read_csv('https://geoip.starlinkisp.net/feed.csv', names=['subnet', 'country', 'state', 'city', 'NaN'], header=None)

    for index, row in geoIp.iterrows():       
        if ipaddress.ip_address(cloudflareIp) in ipaddress.ip_network(row['subnet']): 
            isp = "Starlink"
            pop = re.search("(?<=customer.)(.*)(?=.pop)", socket.gethostbyaddr(cloudflareIp)[0]).group()
            country = pycountry.countries.get(alpha_2=row['country']).name
            city = row['city']
            break

        else:
            isp = "Not Starlink"
            pop = "N/A"
            country = "N/A"
            city = "N/A"
    
    userNetwork = {'ip': cloudflareIp, 'isp': isp, 'pop': pop, 'country': country, 'city': city}

    return render_template('network/index.html', userNetwork=userNetwork)