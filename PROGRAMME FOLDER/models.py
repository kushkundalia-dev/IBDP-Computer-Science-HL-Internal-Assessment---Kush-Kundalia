from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Role(db.Model):
    """User roles: HR Manager, General Manager, Front Desk Agent"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    
    # Relationships
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    
    # Role and status
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_on_duty = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if user has specific role"""
        return self.role.name == role_name
    
    def can_edit(self):
        """Check if user can edit (based on duty status for front desk)"""
        if self.role.name == 'Front Desk Agent':
            return self.is_on_duty
        return True  # Managers and HR can always edit
    
    def __repr__(self):
        return f'<User {self.username}>'

class Guest(db.Model):
    """Guest profile model"""
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20), nullable=False)
    id_proof_type = db.Column(db.String(50))
    id_proof_number = db.Column(db.String(50))
    address = db.Column(db.Text)
    
    # Guest metrics
    total_stays = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_visit = db.Column(db.DateTime)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='guest', lazy=True)
    notes = db.relationship('GuestNote', backref='guest', lazy=True)
    
    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'

class RoomCategory(db.Model):
    """Room categories"""
    __tablename__ = 'room_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Standard Queen, Standard Twin, etc.
    description = db.Column(db.Text)
    size_sqm = db.Column(db.Integer)  # Size in square meters
    max_adults = db.Column(db.Integer, default=2)
    max_children = db.Column(db.Integer, default=1)
    base_price = db.Column(db.Float, nullable=False)
    
    # Relationships
    rooms = db.relationship('Room', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<RoomCategory {self.name}>'

class Room(db.Model):
    """Individual rooms"""
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('room_categories.id'), nullable=False)
    
    # Room status
    status = db.Column(db.String(20), default='available')  # available, occupied, cleaning, maintenance
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='room', lazy=True)
    
    def __repr__(self):
        return f'<Room {self.room_number}>'

class Reservation(db.Model):
    """Reservation/Booking model"""
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    reservation_code = db.Column(db.String(20), unique=True, nullable=False)
    
    # Foreign keys
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    
    # Dates
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    actual_check_in = db.Column(db.DateTime)
    actual_check_out = db.Column(db.DateTime)
    
    # Guests
    num_adults = db.Column(db.Integer, default=1)
    num_children = db.Column(db.Integer, default=0)
    
    # Pricing
    room_rate = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0.0)
    
    # Status
    status = db.Column(db.String(20), default='confirmed')  # confirmed, checked_in, checked_out, cancelled
    
    # Extras
    breakfast_included = db.Column(db.Boolean, default=False)
    special_requests = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    notes = db.relationship('GuestNote', backref='reservation', lazy=True)
    
    def __repr__(self):
        return f'<Reservation {self.reservation_code}>'

class GuestNote(db.Model):
    """Notes added by staff about guests or reservations"""
    __tablename__ = 'guest_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'))
    
    # Note content
    note_text = db.Column(db.Text, nullable=False)
    
    # Approval workflow
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_approved = db.Column(db.Boolean, default=False)
    approval_date = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_notes')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_notes')
    
    def __repr__(self):
        return f'<GuestNote {self.id}>'

class Schedule(db.Model):
    """Staff duty schedule"""
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Schedule details
    shift_date = db.Column(db.Date, nullable=False)
    shift_start = db.Column(db.Time, nullable=False)
    shift_end = db.Column(db.Time, nullable=False)
    
    # Assigned by
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='schedules')
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_schedules')
    
    def __repr__(self):
        return f'<Schedule {self.user_id} on {self.shift_date}>'
