from flask import Blueprint

pullReddit_BP = Blueprint("pullReddit_BP", __name__)
from . import routes

def init_app(app):
    app.register_blueprint(pullReddit_BP)
