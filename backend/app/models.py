import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from app.extensions import db

#Search History Model
class SearchHistory(db.Model):
    __tablename__ = 'searchHistory'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(), nullable=False)
    subreddit = db.Column(db.String(), nullable=False)
    sentimentKeywords = db.Column(db.String(), nullable=False)
    startDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    created_utc = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    
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