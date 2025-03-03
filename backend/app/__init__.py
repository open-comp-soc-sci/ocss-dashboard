from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

from app.extensions import db
from app.routes import main

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:8001"}})
    load_dotenv()
    app.config.from_prefixed_env()
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  

    db.init_app(app)
    app.register_blueprint(main)
    
    return app