from flask import Blueprint

searchHistory_BP = Blueprint("searchHistory_BP", __name__)
from . import routes

def init_app(app):
    app.register_blueprint(searchHistory_BP)
