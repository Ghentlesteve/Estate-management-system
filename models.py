from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='admin')  # admin, staff
    # ADD THIS: Link user login to their resident profile record
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'), nullable=True)
    resident = db.relationship('Resident', backref=db.backref('user_account', uselist=False))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

class Resident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    house_number = db.Column(db.String(20), unique=True, nullable=False)
    occupant_count = db.Column(db.Integer, default=1)
    vehicle_count = db.Column(db.Integer, default=0)
    move_in_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='resident', lazy=True)
    complaints = db.relationship('Complaint', backref='resident', lazy=True)

class DuesCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Monthly Levy, Security, Waste
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), default='monthly')  # monthly, quarterly, yearly
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'), nullable=False)
    dues_category_id = db.Column(db.Integer, db.ForeignKey('dues_category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    payment_method = db.Column(db.String(30))  # cash, transfer, cheque
    reference_number = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed
    receipt_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'), nullable=False)
    category = db.Column(db.String(30))  # Infrastructure, Security, Noise, Other
    subject = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, resolved, closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    assigned_to = db.Column(db.String(50))
    resolution_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30))  # General, Security, Maintenance, Event
    is_urgent = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)