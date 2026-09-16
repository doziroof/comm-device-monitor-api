from flask import Flask

from .api import api
from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(api)
    return app
