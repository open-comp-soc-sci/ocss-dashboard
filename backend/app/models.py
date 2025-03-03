import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from flask_login import UserMixin

from app.extensions import db

#User Model (modify to only have email and as primary to use as foreign key for search?)
class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(14), nullable=False, unique=True)
    password = db.Column(db.String(162), nullable=False)
    #email = db.Column(db.String(100), nullable=False, unique=True)
    
    def get_id(self):
        return str(self.user_id)

#Search History Model
class SearchHistory(db.Model):
    __tablename__ = 'searchHistory'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(), nullable=False)
    search_query = db.Column(db.String(200), nullable=False)
    created_utc = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    #user = db.relationship('Users', backref=db.backref('search_histories', lazy=True))
    
# unimplemented RedditData model class. 
class RedditData(Base):
    __tablename__ = 'redditData'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author = db.Column(db.String(100), nullable=False)
    created_utc = db.Column(db.String(100), nullable=False)
    body = db.Column(db.String(100), nullable=False)
    link_id = db.Column(db.String(100), nullable=False,)
    
    def get_id(self):
        return str(self.id)