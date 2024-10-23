# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

class Food(db.Model):
    __tablename__ = 'food'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Food_Order(db.Model):
    __tablename__ = 'food_order'
    id = db.Column(db.Integer, primary_key=True)
    items = db.Column(db.MutableList.as_mutable(db.PickleType), nullable=False)  # Store items as a list of strings
    total_price = db.Column(db.Float, nullable=False)

class Tracking(db.Model):
    __tablename__ = 'tracking'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('food_order.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
