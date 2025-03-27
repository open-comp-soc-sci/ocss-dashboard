from flask import Blueprint

clickHouse_BP = Blueprint("clickHouse_BP", __name__)
from . import routes

def init_app(app):
    app.register_blueprint(clickHouse_BP)
