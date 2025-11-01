"""Authentication helpers and decorators"""
from functools import wraps
from flask import session, redirect, url_for, jsonify, request


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Check if it's an API request
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Login required'}), 401
            # Otherwise redirect to login page
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current logged-in user data from session"""
    return {
        'user_id': session.get('user_id'),
        'name': session.get('user_name'),
        'email': session.get('user_email')
    }
