import uuid
from sqlalchemy.dialects.postgresql import UUID
from flask_login import UserMixin

from app.extensions import db

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    
    def get_id(self):
        return str(self.user_id)
    #do we want email???
    #email = db.Column(db.String(100), nullable=False, unique=True)

#search history model class