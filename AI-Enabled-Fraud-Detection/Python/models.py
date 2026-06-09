from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    reports = db.relationship('Report', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(64), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    merchant = db.Column(db.String(128), nullable=False)
    merchant_category = db.Column(db.String(64))
    description = db.Column(db.String(255))
    location = db.Column(db.String(128))
    ip_address = db.Column(db.String(64))
    device_id = db.Column(db.String(64))
    is_fraud = db.Column(db.Boolean, default=False)
    fraud_probability = db.Column(db.Float, default=0.0)
    flagged = db.Column(db.Boolean, default=False)
    flagged_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat(),
            'merchant': self.merchant,
            'merchant_category': self.merchant_category,
            'description': self.description,
            'location': self.location,
            'ip_address': self.ip_address,
            'device_id': self.device_id,
            'is_fraud': self.is_fraud,
            'fraud_probability': self.fraud_probability,
            'flagged': self.flagged,
            'flagged_reason': self.flagged_reason
        }

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    fraud_count = db.Column(db.Integer, default=0)
    total_fraud_amount = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'fraud_count': self.fraud_count,
            'total_fraud_amount': self.total_fraud_amount
        }

class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    model_type = db.Column(db.String(64), nullable=False)  # e.g., 'random_forest', 'isolation_forest', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'model_type': self.model_type,
            'created_at': self.created_at.isoformat(),
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'is_active': self.is_active
        }
