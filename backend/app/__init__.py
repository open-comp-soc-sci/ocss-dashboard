from flask_login import LoginManager
from flask import Flask
import os

from app.extensions import db
from app.routes import main
from app.auth import auth
from app.models import Users

def create_app():
    app = Flask(__name__)
    app.config.from_prefixed_env()

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  

    db.init_app(app)

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get((user_id))
    
    return app