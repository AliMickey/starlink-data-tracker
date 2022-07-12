# Starlink Data Tracker
## Description
Community maintained database for Starlink data.

[Live](https://starlinkversions.com)


## Features
### Firmware
As new firmware revisions are constantly released to the public, it made sense to maintain an updated list. This allows us to compare and curate notes for each revision.

### Speedtests
Tracking the performance of any ISP is important, we make use of Speedtest.net's services to store results from users. Data is captured via the website form, the official [Discord](https://discord.gg/Rr2u4ystEe) channel, and through the all-in-one script (in development).


## Motivation
The existing [spreadsheet](https://docs.google.com/spreadsheets/d/1nsdLZ34VVX1qNVlDlAErzLov-fb_ZWgpYAQJWp_W8ic) solution was cumbersome and very messy.


## Technologies Used
[Flask](https://flask.palletsprojects.com),
[Bootstrap](https://getbootstrap.com),
[Docker](https://www.docker.com),


## Build from source
1. Clone the repository
2. Move into the directory `cd starlink-firmware-track`
3. Initialise a virtual environment `python -m venv venv`
4. Activate the virtual environment, Linux: `source venv/bin/activate`
5. Install requirements `pip install -r requirements.txt`
6. Edit the config file with your keys `starlink/instance/config.py`
7. Set Flask environment `export FLASK_APP=starlink`
8. Initialise a new database `flask init-db`
9. Import the most recent dataset `flask import-db`
10. Run the app `flask run`

## Notes
The `databaseBackup.sql` file is archived here for development purposes.