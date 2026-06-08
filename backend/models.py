from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

#Initialize sqlalchemy object
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True ,nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship link to staff profile
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False)

    # Relationship link to trek
    assigned_treks = db.relationship('Trek', backref='manager', lazy=True)

    # The Relationship Link to Bookings (One-to-Many: One user has many bookings)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class StaffProfile(db.Model):
    __tablename__ = 'staff_profile'

    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact_details = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Active')

class Trek(db.Model):
    __tablename__ = 'trek'

    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    location = db.Column(db.String(300), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # The Relationship Link to Bookings (One-to-Many: One trek has many bookings)
    bookings = db.relationship('Booking', backref='trek', lazy=True)

class Booking(db.Model):
    __tablename__ = 'booking'
    
    # The Bridge Columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    
    # Tracking Details
    booking_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Why we use lambda:
    # This is a cool SQLAlchemy trick. If you just wrote default=datetime.now(timezone.utc), 
    # Python would calculate the time right now when you start the server, 
    # and every single booking forever would get that exact same timestamp. 
    # By putting lambda: in front, you are handing SQLAlchemy a tiny set of instructions and saying, 
    # "Don't run this now. Run this exact function only when a user actually clicks the book button."

    status = db.Column(db.String(20), default='Booked')