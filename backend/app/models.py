import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from app.extensions import db

# Search History Model
class SearchHistory(db.Model):
    __tablename__ = 'searchHistory'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(), nullable=False)
    subreddit = db.Column(db.String(), nullable=False)
    startDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    option = db.Column(db.String(), nullable=False)
    created_utc = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

# Results Model
class ResultData(db.Model):
    __tablename__ = 'resultData'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(), nullable=False)
    # Search Parameters
    subreddit = db.Column(db.String(), nullable=False)
    startDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    created_utc = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    # Topic Relationship
    groups = db.relationship(
        "TopicData",
        backref="resultData",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

# Topics Model
class TopicData(db.Model):
    __tablename__ = 'topicData'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(), nullable=False)
    # Topic Info
    result_id = db.Column(db.Integer, db.ForeignKey('resultData.id', ondelete='CASCADE'), nullable=False)
    group_number = db.Column(db.Integer, nullable=False)
    group_label = db.Column(db.String, nullable=False)
    topics = db.Column(db.JSON, nullable=False) # Should include topic number, topic keywords, post count, and topic label
    example_posts = db.Column(db.JSON, nullable=True) # Should include topic number and example posts, will they always have an example post?
    
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