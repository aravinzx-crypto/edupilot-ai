import os
import re
import datetime
from functools import wraps
import bcrypt
import jwt
from flask import request, redirect, url_for, session, jsonify, g
from database import get_db

SECRET_KEY = os.environ.get('EDUPILOT_SECRET_KEY', 'edupilot-ai-production-secret-key-2026')
TOKEN_COOKIE_NAME = 'edupilot_token'
TOKEN_EXPIRY_DAYS = 7

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with a salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def generate_token(user_id: int, email: str, name: str) -> str:
    """Generate a JWT token for the user."""
    payload = {
        'sub': str(user_id),
        'email': email,
        'name': name,
        'iat': datetime.datetime.now(datetime.timezone.utc),
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=TOKEN_EXPIRY_DAYS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token: str):
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except Exception:
        return None

def validate_registration(name: str, email: str, password: str, confirm_password: str):
    """Validate user registration inputs."""
    errors = {}
    if not name or len(name.strip()) < 2:
        errors['name'] = 'Full name must be at least 2 characters long.'
    
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if not email or not re.match(email_regex, email.strip()):
        errors['email'] = 'Please enter a valid email address.'
        
    if not password or len(password) < 6:
        errors['password'] = 'Password must be at least 6 characters long.'
        
    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'
        
    return errors

def get_current_user():
    """Retrieve current authenticated user from token or session."""
    if hasattr(g, 'current_user') and g.current_user is not None:
        return g.current_user

    token = None
    # 1. Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        
    # 2. Check HTTP-only cookie
    if not token:
        token = request.cookies.get(TOKEN_COOKIE_NAME)
        
    # 3. Check Flask session
    if not token and 'token' in session:
        token = session.get('token')

    if not token:
        g.current_user = None
        return None

    payload = decode_token(token)
    if not payload or 'sub' not in payload:
        g.current_user = None
        return None

    try:
        user_id = int(payload['sub'])
    except (ValueError, TypeError):
        g.current_user = None
        return None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, preferred_language, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            user_dict = dict(user)
            g.current_user = user_dict
            return user_dict

    g.current_user = None
    return None

def login_required(f):
    """Decorator to enforce authentication on routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None:
            # Check if this is an API route
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required. Please log in to proceed.'
                }), 401
            # Web page route: redirect to login
            return redirect(url_for('login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
