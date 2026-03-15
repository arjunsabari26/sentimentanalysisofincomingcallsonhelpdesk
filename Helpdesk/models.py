from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='agent') # 'admin' or 'agent'

class CallRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    audio_filename = db.Column(db.String(255), nullable=False)
    transcript = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(50), nullable=True) # Positive, Neutral, Negative
    confidence = db.Column(db.Float, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    summary = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    customer_response = db.Column(db.Text, nullable=True)
