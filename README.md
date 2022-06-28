# Starlink Firmware Track
## Description
Website to make tracking Starlink firmware revisions easier. This is a crowdsourced project and could be incorrect.

[Live Version](https://starlinkversions.com)

## Motivation
The existing spreadsheet solution was cumbersome and very messy.

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