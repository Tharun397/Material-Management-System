from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Role Constants
ROLE_ADMIN = 'Administrator'
ROLE_EMPLOYEE = 'Employee'
ROLE_CUSTODIAN = 'Department Custodian'

class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), default='Internal Material Management System')
    logo_filename = db.Column(db.String(255), default='logo.png')
    footer_text = db.Column(db.String(100), default='Powered by VCS team')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))
    role = db.Column(db.String(50), default=ROLE_EMPLOYEE)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    manufacturer = db.Column(db.String(100))
    model_number = db.Column(db.String(100))
    part_number = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    asset_number = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)
    technical_specifications = db.Column(db.Text)
    condition = db.Column(db.String(50), default='New')
    
    # Ownership
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_holder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    department = db.Column(db.String(100), nullable=False)
    
    # Location Hierarchy
    building = db.Column(db.String(100))
    floor = db.Column(db.String(50))
    room = db.Column(db.String(100))
    rack = db.Column(db.String(50))
    cupboard = db.Column(db.String(50))
    drawer = db.Column(db.String(50))

    # Status: AVAILABLE, BORROWED, RESERVED, UNDER_MAINTENANCE, DAMAGED, LOST, RETIRED
    status = db.Column(db.String(50), default='AVAILABLE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('Category', backref='materials')
    owner = db.relationship('User', foreign_keys=[owner_id])
    current_holder = db.relationship('User', foreign_keys=[current_holder_id])

class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'
    id = db.Column(db.Integer, primary_key=True)
    borrow_id = db.Column(db.String(50), unique=True, nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_return_date = db.Column(db.DateTime, nullable=False)
    actual_return_date = db.Column(db.DateTime, nullable=True)
    purpose = db.Column(db.Text, nullable=False)
    return_condition = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='ACTIVE')  # ACTIVE, RETURNED, OVERDUE
    remarks = db.Column(db.Text)

    material = db.relationship('Material', backref='borrow_records')
    borrower = db.relationship('User', backref='borrowings')

class MaterialHistory(db.Model):
    __tablename__ = 'material_history'
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    remarks = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    performed_by = db.relationship('User')
    material = db.relationship('Material', backref='history')