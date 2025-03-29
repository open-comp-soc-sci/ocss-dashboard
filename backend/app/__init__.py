from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

from app.extensions import db
from app.clickHouse import clickHouse_BP
from app.pullReddit import pullReddit_BP
from app.searchHistory import searchHistory_BP

def create_app():
    app = Flask(__name__)

    cors = CORS(app, resources={r"/api/*": {"origins": ["http://localhost:8001", "http://sunshine.cise.ufl.edu:8001"]}})

    load_dotenv()
    app.config.from_prefixed_env()
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  

    db.init_app(app)
    cors.init_app(app)
    app.register_blueprint(clickHouse_BP)
    app.register_blueprint(pullReddit_BP)
    app.register_blueprint(searchHistory_BP)
    
    return app