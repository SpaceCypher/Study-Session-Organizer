"""Authentication routes - Login, Register, Logout"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.db_manager import DatabaseManager
from config import Config
from utils import validators
import bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET'])
def login():
    """Display login page"""
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login_post():
    """Handle login submission"""
    data = request.get_json() if request.is_json else request.form
    
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    # Validation
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    
    if not validators.validate_email(email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    # Check credentials
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT student_id, name, email, phone, major, year, gpa, learning_style, personality_type, password
            FROM STUDENT 
            WHERE email = %s
        """
        results = db.execute_query(query, (email,))
        
        if not results:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        user = results[0]
        stored_password = user['password']
        
        # Verify password - handle both bcrypt hashed and plain text (for migration)
        password_valid = False
        if stored_password.startswith('$2b$'):
            # Bcrypt hashed password
            password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        else:
            # Plain text password (legacy - for migration period)
            password_valid = (stored_password == password)
            
            # Auto-migrate to bcrypt on successful login
            if password_valid:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                update_query = "UPDATE STUDENT SET password = %s WHERE student_id = %s"
                db.execute_update(update_query, (hashed.decode('utf-8'), user['student_id']))
        
        if not password_valid:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        # Create session
        session['user_id'] = user['student_id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session.permanent = True
        
        return jsonify({
            'success': True, 
            'message': 'Login successful',
            'redirect': url_for('dashboard.index')
        })


@auth_bp.route('/register', methods=['GET'])
def register():
    """Display registration page"""
    return render_template('register.html')


@auth_bp.route('/register', methods=['POST'])
def register_post():
    """Handle registration submission"""
    data = request.get_json() if request.is_json else request.form
    
    # Extract fields
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    srn = data.get('srn', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    major = data.get('major', '').strip()
    year = data.get('year')
    gpa = data.get('gpa')
    learning_style = data.get('learning_style', '').strip()
    personality_type = data.get('personality_type', '').strip()
    
    # Validation
    errors = []
    
    if not name:
        errors.append('Name is required')
    if not email or not validators.validate_email(email):
        errors.append('Valid email is required')
    if not srn:
        errors.append('SRN (Student ID) is required')
    if not phone or not validators.validate_phone(phone):
        errors.append('Valid 10-digit phone number is required')
    if not password or len(password) < 6:
        errors.append('Password must be at least 6 characters')
    if not major:
        errors.append('Major is required')
    if not year or not validators.validate_year(year):
        errors.append('Year must be between 1 and 6')
    if not gpa or not validators.validate_gpa(gpa):
        errors.append('GPA must be between 0.0 and 10.0')
    if not learning_style or not validators.validate_learning_style(learning_style):
        errors.append('Valid learning style is required')
    if not personality_type or not validators.validate_personality_type(personality_type):
        errors.append('Valid personality type is required')
    
    if errors:
        return jsonify({'success': False, 'message': '; '.join(errors)}), 400
    
    # Check if email or SRN already exists
    with DatabaseManager(Config.DB_CONFIG) as db:
        check_query = "SELECT student_id FROM STUDENT WHERE email = %s OR enrollment_id = %s"
        existing = db.execute_query(check_query, (email, srn))
        
        if existing:
            return jsonify({'success': False, 'message': 'Email or SRN already registered'}), 400
        
        # Hash password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert new student
        insert_query = """
            INSERT INTO STUDENT (name, email, enrollment_id, phone, password, major, year, gpa, learning_style, personality_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        result = db.execute_update(insert_query, (name, email, srn, phone, hashed_password.decode('utf-8'), major, year, gpa, learning_style, personality_type))
        
        student_id = result['last_id']
        
        # Auto-login after registration
        session['user_id'] = student_id
        session['user_name'] = name
        session['user_email'] = email
        session.permanent = True
        
        return jsonify({
            'success': True, 
            'message': 'Registration successful',
            'redirect': url_for('dashboard.index')
        })


@auth_bp.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/check')
def check():
    """Check if user is logged in"""
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'user': {
                'id': session['user_id'],
                'name': session['user_name'],
                'email': session['user_email']
            }
        })
    return jsonify({'success': False, 'message': 'Not logged in'}), 401
