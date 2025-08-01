# blueprints/auth.py
"""
Simplified Authentication Blueprint - Core User Authentication System
- User registration (no email verification)
- Login/logout with JWT tokens
- Role-based access control
- Security features (rate limiting, account lockout)
- Session management
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
import re
import logging

# Initialize blueprint
bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.web_app_models import Users, UserTypes, UserSessions
    from models.system_monitoring_models import ErrorLog
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # For development - create mock models
    class Users:
        def __init__(self): pass
        def find_one(self, query): return None
        def create(self, data): return ObjectId()
        def update_by_id(self, id, data): return True
        def count(self, query=None): return 0
        def find_many(self, query, **kwargs): return []
    
    class UserTypes:
        def __init__(self): pass
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
    
    class UserSessions:
        def __init__(self): pass
        def create(self, data): return ObjectId()
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
        def update_many(self, query, update): 
            class MockResult:
                modified_count = 1
            return MockResult()
        def count(self, query=None): return 0
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass


# Initialize models
users_model = Users()
user_types_model = UserTypes()
user_sessions_model = UserSessions()
error_log_model = ErrorLog()


# =====================================================
# HELPER FUNCTIONS & DECORATORS
# =====================================================

def generate_jwt_token(user_id, user_type='citizen', expires_hours=24):
    """Generate JWT token for user authentication"""
    try:
        payload = {
            'user_id': str(user_id),
            'user_type': user_type,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow(),
            'type': 'access_token'
        }
        
        secret_key = current_app.config.get('SECRET_KEY', 'fallback-secret-key')
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return token
    except Exception as e:
        logger.error(f"Failed to generate JWT token: {e}")
        return None

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        secret_key = current_app.config.get('SECRET_KEY', 'fallback-secret-key')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return {'error': 'Token verification failed'}

def auth_required(allowed_roles=None):
    """Decorator to require authentication and optionally specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'message': 'Please provide a valid authentication token'
                }), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify token
            payload = verify_jwt_token(token)
            if 'error' in payload:
                return jsonify({
                    'success': False,
                    'error': 'Authentication failed',
                    'message': payload['error']
                }), 401
            
            # Get user details
            try:
                user = users_model.find_one({'_id': ObjectId(payload['user_id'])})
                if not user:
                    return jsonify({
                        'success': False,
                        'error': 'User not found',
                        'message': 'User account no longer exists'
                    }), 401
                
                # Check if user is active
                if user.get('status') != 'active':
                    return jsonify({
                        'success': False,
                        'error': 'Account inactive',
                        'message': 'Your account has been deactivated'
                    }), 401
                
                # Check role permissions
                if allowed_roles and user.get('user_type_id') not in allowed_roles:
                    return jsonify({
                        'success': False,
                        'error': 'Insufficient permissions',
                        'message': 'You do not have permission to access this resource'
                    }), 403
                
                # Add user info to request context
                request.current_user = {
                    'id': str(user['_id']),
                    'user_type': user.get('user_type_id', 'citizen'),
                    'username': user.get('username'),
                    'email': user.get('email'),
                    'verified': user.get('verified', True)  # Always true for simplified version
                }
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Authentication failed',
                    'message': 'An error occurred during authentication'
                }), 401
        
        return decorated_function
    return decorator

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength - simplified for development"""
    if len(password) < 6:  # Relaxed for development
        return False, "Password must be at least 6 characters long"
    
    return True, "Password is valid"

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


# =====================================================
# CORE AUTHENTICATION ENDPOINTS
# =====================================================

@bp.route('/auth/register', methods=['POST'])
def register():
    """User registration endpoint - simplified version"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': 'Missing required field',
                    'message': f'{field} is required'
                }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        user_type_id = data.get('user_type_id', 'citizen')
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Validate password strength
        is_valid, password_message = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Invalid password',
                'message': password_message
            }), 400
        
        # Check if username already exists
        existing_username = users_model.find_one({'username': username})
        if existing_username:
            return jsonify({
                'success': False,
                'error': 'Username taken',
                'message': 'This username is already taken'
            }), 409
        
        # Check if email already exists
        existing_email = users_model.find_one({'email': email})
        if existing_email:
            return jsonify({
                'success': False,
                'error': 'Email already registered',
                'message': 'An account with this email already exists'
            }), 409
        
        # Validate user type - simplified list for development
        valid_types = ['citizen', 'activist', 'journalist', 'researcher', 'ngo_worker', 'moderator', 'admin']
        if user_type_id not in valid_types:
            user_type_id = 'citizen'  # Default to citizen
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user record - simplified for development
        user_data = {
            'username': username,
            'email': email,
            'password_hash': hashed_password,
            'user_type_id': user_type_id,
            'status': 'active',
            'verified': True,  # Auto-verified for simplified version
            'email_verified': True,  # Auto-verified for simplified version
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_login': None,
            'failed_login_attempts': 0,
            'account_locked_until': None,
            'two_factor_enabled': False,
            'phone_number': data.get('phone_number', ''),
            'profile': {
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'bio': data.get('bio', ''),
                'location': data.get('location', ''),
                'preferred_language': data.get('preferred_language', 'en'),
                'timezone': data.get('timezone', 'UTC')
            },
            'privacy_settings': {
                'profile_public': data.get('profile_public', True),
                'show_activity': data.get('show_activity', True),
                'allow_messages': data.get('allow_messages', True)
            },
            'notification_settings': {
                'email_enabled': data.get('email_notifications', True),
                'sms_enabled': False,
                'push_enabled': data.get('push_notifications', True),
                'alert_frequency': data.get('alert_frequency', 'daily')
            },
            'statistics': {
                'login_count': 0,
                'reports_submitted': 0,
                'reports_verified': 0,
                'posts_created': 0,
                'last_active': None
            }
        }
        
        # Create user
        user_id = users_model.create(user_data)
        
        # Generate JWT token
        jwt_token = generate_jwt_token(user_id, user_type_id)
        
        # Create session record
        session_data = {
            'user_id': user_id,
            'session_token': jwt_token,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=24),
            'active': True,
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'login_method': 'registration'
        }
        
        session_id = user_sessions_model.create(session_data)
        
        logger.info(f"User registered successfully: {username} ({email})")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'data': {
                'user_id': str(user_id),
                'username': username,
                'email': email,
                'user_type': user_type_id,
                'verified': True,  # Always true in simplified version
                'token': jwt_token,
                'session_id': str(session_id),
                'profile': user_data['profile']
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        error_log_model.log_error(
            service_name="auth_service",
            error_type="registration_error",
            error_message=str(e),
            context={'email': data.get('email', 'unknown')},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Registration failed',
            'message': 'An error occurred during registration. Please try again.'
        }), 500


@bp.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'Missing credentials',
                'message': 'Email and password are required'
            }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        remember_me = data.get('remember_me', False)
        
        # Find user by email or username
        user = users_model.find_one({'$or': [{'email': email}, {'username': email}]})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401
        
        # Check if account is locked
        if user.get('account_locked_until') and user['account_locked_until'] > datetime.utcnow():
            return jsonify({
                'success': False,
                'error': 'Account locked',
                'message': f'Account is locked until {user["account_locked_until"].strftime("%Y-%m-%d %H:%M:%S")}'
            }), 423
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            # Increment failed login attempts
            failed_attempts = user.get('failed_login_attempts', 0) + 1
            update_data = {'failed_login_attempts': failed_attempts}
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                update_data['account_locked_until'] = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(f"Account locked due to failed login attempts: {email}")
            
            users_model.update_by_id(user['_id'], update_data)
            
            return jsonify({
                'success': False,
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401
        
        # Check if user is active
        if user.get('status') != 'active':
            return jsonify({
                'success': False,
                'error': 'Account inactive',
                'message': 'Your account has been deactivated. Please contact support.'
            }), 403
        
        # Generate JWT token (longer expiry if remember_me)
        token_hours = 30 * 24 if remember_me else 24  # 30 days vs 24 hours
        jwt_token = generate_jwt_token(user['_id'], user.get('user_type_id', 'citizen'), token_hours)
        
        # Update user login info
        login_update = {
            'last_login': datetime.utcnow(),
            'failed_login_attempts': 0,
            'account_locked_until': None,
            'statistics.login_count': user.get('statistics', {}).get('login_count', 0) + 1,
            'statistics.last_active': datetime.utcnow()
        }
        
        users_model.update_by_id(user['_id'], login_update)
        
        # Create session record
        session_data = {
            'user_id': user['_id'],
            'session_token': jwt_token,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=token_hours),
            'active': True,
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'login_method': 'password',
            'remember_me': remember_me
        }
        
        session_id = user_sessions_model.create(session_data)
        
        logger.info(f"User logged in successfully: {user['username']} ({user['email']})")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user_id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'user_type': user.get('user_type_id', 'citizen'),
                'verified': True,  # Always true in simplified version
                'token': jwt_token,
                'session_id': str(session_id),
                'expires_at': (datetime.utcnow() + timedelta(hours=token_hours)).isoformat(),
                'profile': user.get('profile', {}),
                'settings': {
                    'notifications': user.get('notification_settings', {}),
                    'privacy': user.get('privacy_settings', {})
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        error_log_model.log_error(
            service_name="auth_service",
            error_type="login_error",
            error_message=str(e),
            context={'email': data.get('email', 'unknown')},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Login failed',
            'message': 'An error occurred during login. Please try again.'
        }), 500


@bp.route('/auth/logout', methods=['POST'])
@auth_required()
def logout():
    """User logout endpoint"""
    try:
        user_id = request.current_user['id']
        
        # Get token from header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header else None
        
        if token:
            # Deactivate the session
            user_sessions_model.update_many(
                {'user_id': ObjectId(user_id), 'session_token': token},
                {'active': False, 'logged_out_at': datetime.utcnow()}
            )
        
        logger.info(f"User logged out: {request.current_user['username']}")
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'Logout failed',
            'message': 'An error occurred during logout'
        }), 500


@bp.route('/auth/check-token', methods=['GET'])
@auth_required()
def check_token():
    """Check if current token is valid"""
    try:
        return jsonify({
            'success': True,
            'message': 'Token is valid',
            'data': {
                'user': request.current_user,
                'authenticated': True
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Token check failed',
            'message': 'An error occurred while checking token'
        }), 500


@bp.route('/auth/refresh-token', methods=['POST'])
@auth_required()
def refresh_token():
    """Refresh user's authentication token"""
    try:
        user_id = request.current_user['id']
        user_type = request.current_user['user_type']
        
        # Generate new token
        new_token = generate_jwt_token(user_id, user_type, expires_hours=24)
        
        # Create new session record
        session_data = {
            'user_id': ObjectId(user_id),
            'session_token': new_token,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=24),
            'active': True,
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'login_method': 'token_refresh'
        }
        
        session_id = user_sessions_model.create(session_data)
        
        return jsonify({
            'success': True,
            'message': 'Token refreshed successfully',
            'data': {
                'token': new_token,
                'session_id': str(session_id),
                'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                'user': request.current_user
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'error': 'Token refresh failed',
            'message': 'An error occurred while refreshing token'
        }), 500


# =====================================================
# UTILITY ENDPOINTS
# =====================================================

@bp.route('/auth/user-types', methods=['GET'])
def get_user_types():
    """Get available user types for registration"""
    try:
        # Simplified user types for development
        user_types = [
            {
                'id': 'citizen',
                'name': 'Concerned Citizen',
                'description': 'Regular users who want to stay informed about social justice issues',
                'requires_verification': False,
                'max_exports_per_day': 3,
                'max_alerts': 5
            },
            {
                'id': 'activist',
                'name': 'Activist',
                'description': 'Active participants in social movements',
                'requires_verification': False,  # Simplified for development
                'max_exports_per_day': 10,
                'max_alerts': 15
            },
            {
                'id': 'journalist',
                'name': 'Journalist/Media',
                'description': 'Verified journalists and media professionals',
                'requires_verification': False,  # Simplified for development
                'max_exports_per_day': 50,
                'max_alerts': 25
            },
            {
                'id': 'researcher',
                'name': 'Academic Researcher',
                'description': 'Academic researchers studying social movements',
                'requires_verification': False,  # Simplified for development
                'max_exports_per_day': 100,
                'max_alerts': 20
            },
            {
                'id': 'ngo_worker',
                'name': 'NGO Worker',
                'description': 'Workers from NGOs and human rights organizations',
                'requires_verification': False,  # Simplified for development
                'max_exports_per_day': 30,
                'max_alerts': 30
            }
        ]
        
        return jsonify({
            'success': True,
            'message': 'User types retrieved successfully',
            'data': {
                'user_types': user_types
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user types error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user types',
            'message': 'An error occurred while retrieving user types'
        }), 500


@bp.route('/auth/check-availability', methods=['POST'])
def check_availability():
    """Check if username or email is available"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        result = {}
        
        # Check username availability
        if 'username' in data:
            username = data['username'].strip()
            if len(username) < 3:
                result['username'] = {
                    'available': False,
                    'message': 'Username must be at least 3 characters long'
                }
            else:
                existing_username = users_model.find_one({'username': username})
                result['username'] = {
                    'available': existing_username is None,
                    'message': 'Username is available' if existing_username is None else 'Username is already taken'
                }
        
        # Check email availability
        if 'email' in data:
            email = data['email'].strip().lower()
            if not validate_email(email):
                result['email'] = {
                    'available': False,
                    'message': 'Invalid email format'
                }
            else:
                existing_email = users_model.find_one({'email': email})
                result['email'] = {
                    'available': existing_email is None,
                    'message': 'Email is available' if existing_email is None else 'Email is already registered'
                }
        
        return jsonify({
            'success': True,
            'message': 'Availability check completed',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Check availability error: {e}")
        return jsonify({
            'success': False,
            'error': 'Availability check failed',
            'message': 'An error occurred while checking availability'
        }), 500


@bp.route('/auth/validate-password', methods=['POST'])
def validate_password_endpoint():
    """Validate password strength - simplified for development"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'Missing password',
                'message': 'Password is required'
            }), 400
        
        is_valid, message = validate_password(password)
        
        # Simplified requirements for development
        requirements = {
            'min_length': len(password) >= 6,
            'not_empty': len(password.strip()) > 0
        }
        
        # Calculate strength score
        strength_score = sum(requirements.values()) / len(requirements)
        
        if strength_score >= 1.0:
            strength = 'good'
        elif strength_score >= 0.5:
            strength = 'fair'
        else:
            strength = 'weak'
        
        return jsonify({
            'success': True,
            'message': 'Password validation completed',
            'data': {
                'is_valid': is_valid,
                'message': message,
                'strength': strength,
                'strength_score': strength_score,
                'requirements': requirements
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Password validation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Password validation failed',
            'message': 'An error occurred while validating password'
        }), 500


# =====================================================
# SESSION MANAGEMENT
# =====================================================

@bp.route('/auth/sessions', methods=['GET'])
@auth_required()
def get_user_sessions():
    """Get user's active sessions"""
    try:
        user_id = request.current_user['id']
        
        # Get active sessions for user
        sessions = list(user_sessions_model.find_many({
            'user_id': ObjectId(user_id),
            'active': True,
            'expires_at': {'$gt': datetime.utcnow()}
        }))
        
        # Format session data (remove sensitive info)
        formatted_sessions = []
        current_token = request.headers.get('Authorization', '').split(' ')[1]
        
        for session in sessions:
            formatted_sessions.append({
                'session_id': str(session['_id']),
                'created_at': session['created_at'].isoformat(),
                'expires_at': session['expires_at'].isoformat(),
                'user_agent': session.get('user_agent', ''),
                'ip_address': session.get('ip_address', ''),
                'login_method': session.get('login_method', ''),
                'is_current': session['session_token'] == current_token
            })
        
        return jsonify({
            'success': True,
            'message': 'Sessions retrieved successfully',
            'data': {
                'sessions': formatted_sessions,
                'total_sessions': len(formatted_sessions)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve sessions',
            'message': 'An error occurred while retrieving sessions'
        }), 500


@bp.route('/auth/sessions/revoke-all', methods=['POST'])
@auth_required()
def revoke_all_sessions():
    """Revoke all user sessions except current one"""
    try:
        user_id = request.current_user['id']
        
        # Get current session token
        current_token = request.headers.get('Authorization', '').split(' ')[1]
        
        # Deactivate all sessions except current one
        result = user_sessions_model.update_many(
            {
                'user_id': ObjectId(user_id),
                'active': True,
                'session_token': {'$ne': current_token}
            },
            {
                'active': False,
                'logged_out_at': datetime.utcnow(),
                'revoked_by': 'user_revoke_all'
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Revoked {result.modified_count} sessions successfully',
            'data': {
                'revoked_count': result.modified_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Revoke all sessions error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to revoke sessions',
            'message': 'An error occurred while revoking sessions'
        }), 500


# =====================================================
# ADMIN ENDPOINTS (Simplified)
# =====================================================

@bp.route('/auth/admin/user-stats', methods=['GET'])
@auth_required(allowed_roles=['admin', 'moderator'])
def get_user_stats():
    """Get user statistics (admin only)"""
    try:
        # Basic user statistics
        total_users = users_model.count()
        active_users = users_model.count({'status': 'active'})
        
        # Users by type
        user_type_stats = {}
        for user_type in ['citizen', 'activist', 'journalist', 'researcher', 'ngo_worker', 'moderator', 'admin']:
            count = users_model.count({'user_type_id': user_type})
            if count > 0:
                user_type_stats[user_type] = count
        
        # Recent registrations (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_registrations = users_model.count({'created_at': {'$gte': seven_days_ago}})
        
        # Active sessions
        active_sessions = user_sessions_model.count({
            'active': True,
            'expires_at': {'$gt': datetime.utcnow()}
        })
        
        return jsonify({
            'success': True,
            'message': 'User statistics retrieved successfully',
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'user_type_distribution': user_type_stats,
                'recent_registrations': recent_registrations,
                'active_sessions': active_sessions
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user statistics',
            'message': 'An error occurred while retrieving user statistics'
        }), 500


# =====================================================
# PLACEHOLDERS FOR FUTURE EMAIL FEATURES
# =====================================================

@bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """TODO: Password reset functionality (requires email setup)"""
    return jsonify({
        'success': False,
        'error': 'Feature not implemented',
        'message': 'Password reset functionality will be implemented when email service is configured'
    }), 501


@bp.route('/auth/verify-email', methods=['POST'])
def verify_email():
    """TODO: Email verification functionality (requires email setup)"""
    return jsonify({
        'success': False,
        'error': 'Feature not implemented',
        'message': 'Email verification is disabled in development mode. All accounts are auto-verified.'
    }), 501


@bp.route('/auth/resend-verification', methods=['POST'])
def resend_verification():
    """TODO: Resend verification email functionality (requires email setup)"""
    return jsonify({
        'success': False,
        'error': 'Feature not implemented',
        'message': 'Email verification is disabled in development mode. All accounts are auto-verified.'
    }), 501


# =====================================================
# HEALTH CHECK & STATUS
# =====================================================

@bp.route('/auth/health', methods=['GET'])
def auth_health_check():
    """Authentication service health check"""
    try:
        # Test database connectivity
        test_count = users_model.count()
        
        return jsonify({
            'success': True,
            'message': 'Authentication service is healthy',
            'data': {
                'service': 'auth_service',
                'status': 'healthy',
                'database_connected': True,
                'total_users': test_count,
                'features': {
                    'registration': True,
                    'login': True,
                    'email_verification': False,  # Disabled for development
                    'password_reset': False,      # Disabled for development
                    'jwt_tokens': True,
                    'session_management': True,
                    'role_based_access': True
                },
                'development_mode': True,
                'notes': [
                    'Email verification is disabled - all accounts are auto-verified',
                    'Password requirements are relaxed for development',
                    'Password reset is disabled - use direct database access if needed'
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Auth health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Authentication service unhealthy',
            'message': str(e)
        }), 500


# =====================================================
# DEVELOPMENT HELPERS
# =====================================================

@bp.route('/auth/dev/create-admin', methods=['POST'])
def create_admin_user():
    """Development helper: Create admin user quickly"""
    try:
        # Only allow in development mode
        if not current_app.debug:
            return jsonify({
                'success': False,
                'error': 'Development only',
                'message': 'This endpoint is only available in development mode'
            }), 403
        
        # Check if admin already exists
        existing_admin = users_model.find_one({'user_type_id': 'admin'})
        if existing_admin:
            return jsonify({
                'success': False,
                'error': 'Admin exists',
                'message': 'An admin user already exists',
                'data': {
                    'existing_admin': {
                        'username': existing_admin['username'],
                        'email': existing_admin['email']
                    }
                }
            }), 409
        
        # Create admin user with default credentials
        admin_data = {
            'username': 'admin',
            'email': 'admin@protesttracker.dev',
            'password_hash': hash_password('admin123'),
            'user_type_id': 'admin',
            'status': 'active',
            'verified': True,
            'email_verified': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_login': None,
            'failed_login_attempts': 0,
            'profile': {
                'first_name': 'System',
                'last_name': 'Administrator',
                'bio': 'Development admin account',
                'location': 'Development Environment'
            },
            'statistics': {
                'login_count': 0,
                'reports_submitted': 0,
                'reports_verified': 0,
                'posts_created': 0
            }
        }
        
        user_id = users_model.create(admin_data)
        
        return jsonify({
            'success': True,
            'message': 'Admin user created successfully',
            'data': {
                'user_id': str(user_id),
                'username': 'admin',
                'email': 'admin@protesttracker.dev',
                'password': 'admin123',
                'note': 'Development admin account created. Change password in production!'
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Create admin error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create admin',
            'message': str(e)
        }), 500


@bp.route('/auth/dev/test-users', methods=['POST'])
def create_test_users():
    """Development helper: Create test users for different roles"""
    try:
        # Only allow in development mode
        if not current_app.debug:
            return jsonify({
                'success': False,
                'error': 'Development only',
                'message': 'This endpoint is only available in development mode'
            }), 403
        
        test_users = [
            {
                'username': 'citizen_test',
                'email': 'citizen@test.com',
                'password': 'test123',
                'user_type_id': 'citizen',
                'first_name': 'Test',
                'last_name': 'Citizen'
            },
            {
                'username': 'activist_test',
                'email': 'activist@test.com',
                'password': 'test123',
                'user_type_id': 'activist',
                'first_name': 'Test',
                'last_name': 'Activist'
            },
            {
                'username': 'journalist_test',
                'email': 'journalist@test.com',
                'password': 'test123',
                'user_type_id': 'journalist',
                'first_name': 'Test',
                'last_name': 'Journalist'
            }
        ]
        
        created_users = []
        
        for user_info in test_users:
            # Check if user already exists
            existing = users_model.find_one({'email': user_info['email']})
            if existing:
                continue
            
            user_data = {
                'username': user_info['username'],
                'email': user_info['email'],
                'password_hash': hash_password(user_info['password']),
                'user_type_id': user_info['user_type_id'],
                'status': 'active',
                'verified': True,
                'email_verified': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'profile': {
                    'first_name': user_info['first_name'],
                    'last_name': user_info['last_name'],
                    'bio': f'Test {user_info["user_type_id"]} account for development'
                },
                'statistics': {
                    'login_count': 0,
                    'reports_submitted': 0,
                    'reports_verified': 0,
                    'posts_created': 0
                }
            }
            
            user_id = users_model.create(user_data)
            created_users.append({
                'user_id': str(user_id),
                'username': user_info['username'],
                'email': user_info['email'],
                'user_type': user_info['user_type_id'],
                'password': user_info['password']
            })
        
        return jsonify({
            'success': True,
            'message': f'Created {len(created_users)} test users',
            'data': {
                'created_users': created_users,
                'note': 'All test users have password: test123'
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Create test users error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create test users',
            'message': str(e)
        }), 500


# =====================================================
# ERROR HANDLERS
# =====================================================

@bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad Request',
        'message': 'The request could not be understood by the server'
    }), 400

@bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication is required to access this resource'
    }), 401

@bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource'
    }), 403

@bp.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred. Please try again later.'
    }), 500


# Export the auth_required decorator for use in other blueprints
__all__ = ['bp', 'auth_required']