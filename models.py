from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin / staff


class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)
    options = db.Column(db.Text, nullable=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    required = db.Column(db.Boolean, default=False)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))