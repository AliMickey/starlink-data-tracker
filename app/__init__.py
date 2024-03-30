import os
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mobility import Mobility

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # from . import scheduler
    # app.before_first_request(scheduler.schedInitJobs)

    from app.functions import db
    db.init_app(app)

    from app.views import auth
    app.register_blueprint(auth.bp)

    from app.views import firmware
    app.register_blueprint(firmware.bp)

    from app.views import speedtests
    app.register_blueprint(speedtests.bp)

    from app.views import network
    app.register_blueprint(network.bp)

    from app.views import shop
    app.register_blueprint(shop.bp)

    from app.views import main
    app.register_blueprint(main.bp)
    app.add_url_rule('/', endpoint='index')

    Mobility(app)
    limiter = Limiter(key_func=get_remote_address)
    limiter.init_app(app)
    limiter.limit("2/second")(auth.bp)
    limiter.limit("2/second")(firmware.bp)
    limiter.limit("2/second")(speedtests.bp)
    limiter.limit("2/second")(network.bp)
    limiter.limit("2/second")(shop.bp)
    limiter.limit("2/second")(main.bp)
    
    return app