import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

db = SQLAlchemy(app)

# --- Database Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='Employee')
    password_hash = db.Column(db.String(255), nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='AVAILABLE')
    category = db.relationship('Category', backref='materials')

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), default='Internal Material Management System')
    footer_text = db.Column(db.String(150), default='© Material Management System')
    logo_filename = db.Column(db.String(100), default='default_logo.png')

# Inject Site Settings globally for templates
@app.context_processor
def inject_site_settings():
    setting = SiteSetting.query.first()
    if not setting:
        setting = SiteSetting(
            site_title='Internal Material Management System',
            footer_text='© Material Management System',
            logo_filename='default_logo.png'
        )
        db.session.add(setting)
        db.session.commit()
    return dict(site_setting=setting)

# --- Routes ---

@app.route('/')
def home():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        emp_id = request.form.get('employee_id')
        password = request.form.get('password')

        if emp_id == 'ADMIN001' and password == 'Admin@123':
            session['user_id'] = 1
            session['employee_id'] = 'ADMIN001'
            session['full_name'] = 'System Administrator'
            session['role'] = 'Administrator'
            flash('Logged in successfully as System Administrator!', 'success')
            return redirect(url_for('dashboard'))

        user = User.query.filter_by(employee_id=emp_id).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['employee_id'] = user.employee_id
            session['full_name'] = user.full_name
            session['role'] = user.role
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Employee ID or Password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/materials')
def materials():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    materials_list = Material.query.all()
    categories = Category.query.all()
    return render_template('materials.html', materials=materials_list, categories=categories)

@app.route('/add-material', methods=['GET', 'POST'])
def add_material():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        cat_id = request.form.get('category_id')
        dept = request.form.get('department')
        
        new_item = Material(
            name=name,
            category_id=int(cat_id) if cat_id else None,
            department=dept,
            status='AVAILABLE'
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Material added successfully!', 'success')
        return redirect(url_for('materials'))

    categories = Category.query.all()
    return render_template('add_material.html', categories=categories)

@app.route('/borrowings')
def borrow_records():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('borrow_records.html', records=[])

@app.route('/users', methods=['GET', 'POST'])
def manage_users():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        emp_id = request.form.get('employee_id')
        name = request.form.get('full_name')
        email = request.form.get('email')
        dept = request.form.get('department')
        role = request.form.get('role', 'Employee')
        pwd = request.form.get('password')

        if User.query.filter_by(employee_id=emp_id).first():
            flash('User with this Employee ID already exists.', 'error')
        else:
            hashed_pwd = generate_password_hash(pwd)
            new_user = User(
                employee_id=emp_id,
                full_name=name,
                email=email,
                department=dept,
                role=role,
                password_hash=hashed_pwd
            )
            db.session.add(new_user)
            db.session.commit()
            flash(f'User {name} created successfully!', 'success')

    users_list = User.query.all()
    return render_template('user.html', users=users_list)

@app.route('/admin-settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('user_id') or session.get('role') != 'Administrator':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('dashboard'))

    setting = SiteSetting.query.first()
    if request.method == 'POST':
        setting.site_title = request.form.get('site_title', setting.site_title)
        setting.footer_text = request.form.get('footer_text', setting.footer_text)

        file = request.files.get('logo')
        if file and file.filename != '':
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            setting.logo_filename = filename

        db.session.commit()
        flash('Admin branding settings updated successfully!', 'success')

    return render_template('admin_settings.html', site_setting=setting)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)