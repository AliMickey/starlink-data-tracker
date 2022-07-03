import sqlite3, click, os
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.path.join(current_app.instance_path, current_app.config['DATABASE']),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(backup=False):
    db = get_db()
    schemaName = 'schema.sql'
    if backup:
        schemaName = 'databaseBackup.sql'
    with current_app.open_resource('schema/' + schemaName) as f:
        db.executescript(f.read().decode('utf8'))

# Clear the existing data and create new tables
@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

# Commit latest data to database
@click.command('import-db')
@with_appcontext
def import_db_command():
    init_db(backup=True)
    click.echo('Imported the database.')
    
def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(import_db_command)