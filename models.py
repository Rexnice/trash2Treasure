from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'household' or 'company'
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    waste_items = db.relationship('WasteItem', backref='user', lazy=True)
    pickups = db.relationship('PickupRequest', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class WasteItem(db.Model):
    __tablename__ = 'waste_items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    waste_type = db.Column(db.String(50), nullable=False)  # plastic, paper, glass, metal, electronic, etc.
    material = db.Column(db.String(100))
    weight_kg = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, scheduled, collected, processed
    points_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_pickup = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<WasteItem {self.waste_type} - {self.weight_kg}kg>'

class PickupRequest(db.Model):
    __tablename__ = 'pickup_requests'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    waste_item_id = db.Column(db.String(36), db.ForeignKey('waste_items.id'), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, en_route, completed, cancelled
    address = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    waste_item = db.relationship('WasteItem', backref='pickup_requests', lazy=True)
    company = db.relationship('User', foreign_keys=[company_id], backref='company_pickups')
    
    def __repr__(self):
        return f'<PickupRequest {self.id}>'

class Reward(db.Model):
    __tablename__ = 'rewards'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(50))  # waste_submission, referral, bonus
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='rewards')
    
    def __repr__(self):
        return f'<Reward {self.points} points>'