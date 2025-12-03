from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize ONLY here
db = SQLAlchemy()

class FDUser(db.Model):
    __tablename__ = 'FDUser'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    face_encoding = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with FDLoginHistory
    login_history = db.relationship("FDLoginHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FDUser ID={self.id}, Username={self.username}>"

class FDLoginHistory(db.Model):
    __tablename__ = 'FDLoginHistory'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('FDUser.id'), nullable=False)
    success = db.Column(db.Boolean, default=True)
    # ADDED THIS MISSING COLUMN:
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with FDUser
    user = db.relationship("FDUser", back_populates="login_history")

    def __repr__(self):
        # Now this works because self.timestamp exists
        return f"<FDLoginHistory UserID={self.user_id}, Time={self.timestamp}>"