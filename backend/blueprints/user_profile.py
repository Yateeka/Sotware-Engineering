# blueprints/user_profile.py
"""
User Profile Blueprint - User Profile & Settings Management
- User profile viewing and editing
- Settings management (notifications, privacy)
- Password changes
- Account management
- User statistics and activity
- Simplified version without email dependencies
"""

import os
import bcrypt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
import re
import logging

# Initialize blueprint
bp = Blueprint('user_profile', __name__)
logger = logging.getLogger(__name__)

# Import auth decorator
try:
    from blueprints.auth import auth_required, validate_password, hash_password, verify_password
except ImportError:
    # Mock for development
    def auth_required(allowed_roles=None):
        def decorator(f):
            def decorated_function(*args, **kwargs):
                request.current_user = {
                    'id': 'mock_user_id', 
                    'user_type': 'citizen',
                    'username': 'mockuser',
                    'email': 'mock@example.com'
                }
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def validate_password(password):
        return len(password) >= 6, "Password must be at least 6 characters"
    
    def hash_password(password):
        return "hashed_" + password
    
    def verify_password(password, hashed):
        return hashed == "hashed_" + password

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.web_app_models import Users, UserTypes, UserSessions, UserReports, Posts
    from models.system_monitoring_models import ErrorLog
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # Mock models for development
    class Users:
        def __init__(self): pass
        def find_one(self, query): return None
        def update_by_id(self, id, data): return True
        def count(self, query=None): return 0
        def find_many(self, query, **kwargs): return []
    
    class UserTypes:
        def __init__(self): pass
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
    
    class UserSessions:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
    
    class UserReports:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
    
    class Posts:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass

# Initialize models
users_model = Users()
user_types_model = UserTypes()
user_sessions_model = UserSessions()
user_reports_model = UserReports()
posts_model = Posts()
error_log_model = ErrorLog()


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def format_user_profile(user, include_private=False, include_statistics=False):
    """Format user profile data for API response"""
    try:
        if not user:
            return None
        
        # Basic profile information
        profile = {
            'user_id': str(user['_id']),
            'username': user.get('username', ''),
            'user_type': user.get('user_type_id', 'citizen'),
            'status': user.get('status', 'active'),
            'verified': user.get('verified', False),
            'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
            'profile': {
                'first_name': user.get('profile', {}).get('first_name', ''),
                'last_name': user.get('profile', {}).get('last_name', ''),
                'bio': user.get('profile', {}).get('bio', ''),
                'location': user.get('profile', {}).get('location', ''),
                'preferred_language': user.get('profile', {}).get('preferred_language', 'en'),
                'timezone': user.get('profile', {}).get('timezone', 'UTC')
            }
        }
        
        # Include private information for own profile
        if include_private:
            profile['email'] = user.get('email', '')
            profile['phone_number'] = user.get('phone_number', '')
            profile['privacy_settings'] = user.get('privacy_settings', {})
            profile['notification_settings'] = user.get('notification_settings', {})
            profile['last_login'] = user.get('last_login').isoformat() if user.get('last_login') else None
        
        # Include statistics if requested
        if include_statistics:
            stats = user.get('statistics', {})
            profile['statistics'] = {
                'login_count': stats.get('login_count', 0),
                'reports_submitted': stats.get('reports_submitted', 0),
                'reports_verified': stats.get('reports_verified', 0),
                'posts_created': stats.get('posts_created', 0),
                'last_active': stats.get('last_active').isoformat() if stats.get('last_active') else None
            }
        
        return profile
        
    except Exception as e:
        logger.error(f"Error formatting user profile: {e}")
        return None

def validate_profile_data(data):
    """Validate profile update data"""
    errors = []
    
    # Validate first name
    first_name = data.get('first_name', '').strip()
    if len(first_name) > 50:
        errors.append('First name must be 50 characters or less')
    
    # Validate last name
    last_name = data.get('last_name', '').strip()
    if len(last_name) > 50:
        errors.append('Last name must be 50 characters or less')
    
    # Validate bio
    bio = data.get('bio', '').strip()
    if len(bio) > 500:
        errors.append('Bio must be 500 characters or less')
    
    # Validate location
    location = data.get('location', '').strip()
    if len(location) > 100:
        errors.append('Location must be 100 characters or less')
    
    # Validate language
    preferred_language = data.get('preferred_language', 'en')
    valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ar', 'zh', 'ja', 'ko', 'ru']
    if preferred_language not in valid_languages:
        errors.append('Invalid language selection')
    
    # Validate timezone
    timezone = data.get('timezone', 'UTC')
    # Basic timezone validation - you might want to use pytz for more comprehensive validation
    if not timezone or len(timezone) > 50:
        errors.append('Invalid timezone')
    
    return errors

def can_view_profile(target_user, requesting_user_id=None):
    """Check if user can view another user's profile based on privacy settings"""
    if not target_user:
        return False
    
    # User can always view their own profile
    if requesting_user_id and str(target_user['_id']) == str(requesting_user_id):
        return True
    
    # Check privacy settings
    privacy_settings = target_user.get('privacy_settings', {})
    profile_public = privacy_settings.get('profile_public', True)
    
    return profile_public


# =====================================================
# USER PROFILE ENDPOINTS
# =====================================================

@bp.route('/user/profile', methods=['GET'])
@auth_required()
def get_current_user_profile():
    """Get current user's profile"""
    try:
        user_id = request.current_user['id']
        
        # Get user from database
        user = users_model.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Format profile with private information and statistics
        profile = format_user_profile(user, include_private=True, include_statistics=True)
        
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Profile formatting error',
                'message': 'An error occurred while formatting your profile'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': {
                'profile': profile
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user profile error: {e}")
        error_log_model.log_error(
            service_name="user_profile_api",
            error_type="get_profile_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve profile',
            'message': 'An error occurred while retrieving your profile'
        }), 500


@bp.route('/user/profile', methods=['PUT'])
@auth_required()
def update_user_profile():
    """Update current user's profile"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Validate profile data
        validation_errors = validate_profile_data(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'message': 'Profile data validation failed',
                'details': validation_errors
            }), 400
        
        # Build update data
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        # Update profile fields
        profile_updates = {}
        for field in ['first_name', 'last_name', 'bio', 'location', 'preferred_language', 'timezone']:
            if field in data:
                profile_updates[field] = data[field].strip() if isinstance(data[field], str) else data[field]
        
        if profile_updates:
            for key, value in profile_updates.items():
                update_data[f'profile.{key}'] = value
        
        # Update phone number if provided
        if 'phone_number' in data:
            update_data['phone_number'] = data['phone_number'].strip()
        
        # Update user in database
        success = users_model.update_by_id(ObjectId(user_id), update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update profile in database'
            }), 500
        
        # Get updated user data
        updated_user = users_model.find_one({'_id': ObjectId(user_id)})
        updated_profile = format_user_profile(updated_user, include_private=True)
        
        logger.info(f"Profile updated for user: {request.current_user['username']}")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'profile': updated_profile
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update user profile error: {e}")
        error_log_model.log_error(
            service_name="user_profile_api",
            error_type="update_profile_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to update profile',
            'message': 'An error occurred while updating your profile'
        }), 500


@bp.route('/user/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get another user's public profile"""
    try:
        # Validate user ID
        if not ObjectId.is_valid(user_id):
            return jsonify({
                'success': False,
                'error': 'Invalid user ID',
                'message': 'The provided user ID is not valid'
            }), 400
        
        # Get user from database
        user = users_model.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'The requested user could not be found'
            }), 404
        
        # Check if profile can be viewed
        requesting_user_id = getattr(request, 'current_user', {}).get('id')
        if not can_view_profile(user, requesting_user_id):
            return jsonify({
                'success': False,
                'error': 'Profile private',
                'message': 'This user\'s profile is private'
            }), 403
        
        # Format profile (no private information for other users)
        include_private = requesting_user_id == user_id
        profile = format_user_profile(user, include_private=include_private, include_statistics=True)
        
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Profile formatting error',
                'message': 'An error occurred while formatting the profile'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': {
                'profile': profile
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve profile',
            'message': 'An error occurred while retrieving the profile'
        }), 500


# =====================================================
# SETTINGS MANAGEMENT
# =====================================================

@bp.route('/user/settings', methods=['GET'])
@auth_required()
def get_user_settings():
    """Get current user's settings"""
    try:
        user_id = request.current_user['id']
        
        # Get user from database
        user = users_model.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Format settings
        settings = {
            'privacy_settings': user.get('privacy_settings', {
                'profile_public': True,
                'show_activity': True,
                'allow_messages': True
            }),
            'notification_settings': user.get('notification_settings', {
                'email_enabled': True,
                'sms_enabled': False,
                'push_enabled': True,
                'alert_frequency': 'daily'
            }),
            'account_preferences': {
                'preferred_language': user.get('profile', {}).get('preferred_language', 'en'),
                'timezone': user.get('profile', {}).get('timezone', 'UTC'),
                'two_factor_enabled': user.get('two_factor_enabled', False)
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'Settings retrieved successfully',
            'data': {
                'settings': settings
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user settings error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve settings',
            'message': 'An error occurred while retrieving your settings'
        }), 500


@bp.route('/user/settings', methods=['PUT'])
@auth_required()
def update_user_settings():
    """Update current user's settings"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Build update data
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        # Update privacy settings
        if 'privacy_settings' in data:
            privacy = data['privacy_settings']
            for key in ['profile_public', 'show_activity', 'allow_messages']:
                if key in privacy and isinstance(privacy[key], bool):
                    update_data[f'privacy_settings.{key}'] = privacy[key]
        
        # Update notification settings
        if 'notification_settings' in data:
            notifications = data['notification_settings']
            for key in ['email_enabled', 'sms_enabled', 'push_enabled']:
                if key in notifications and isinstance(notifications[key], bool):
                    update_data[f'notification_settings.{key}'] = notifications[key]
            
            # Update alert frequency
            if 'alert_frequency' in notifications:
                valid_frequencies = ['immediate', 'daily', 'weekly', 'disabled']
                if notifications['alert_frequency'] in valid_frequencies:
                    update_data['notification_settings.alert_frequency'] = notifications['alert_frequency']
        
        # Update account preferences
        if 'account_preferences' in data:
            prefs = data['account_preferences']
            
            # Update language
            if 'preferred_language' in prefs:
                valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ar', 'zh', 'ja', 'ko', 'ru']
                if prefs['preferred_language'] in valid_languages:
                    update_data['profile.preferred_language'] = prefs['preferred_language']
            
            # Update timezone
            if 'timezone' in prefs and prefs['timezone']:
                update_data['profile.timezone'] = prefs['timezone']
        
        # Update user in database
        success = users_model.update_by_id(ObjectId(user_id), update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update settings in database'
            }), 500
        
        logger.info(f"Settings updated for user: {request.current_user['username']}")
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Update user settings error: {e}")
        error_log_model.log_error(
            service_name="user_profile_api",
            error_type="update_settings_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to update settings',
            'message': 'An error occurred while updating your settings'
        }), 500


# =====================================================
# PASSWORD MANAGEMENT
# =====================================================

@bp.route('/user/password', methods=['PUT'])
@auth_required()
def change_password():
    """Change user's password"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': 'Missing passwords',
                'message': 'Current password and new password are required'
            }), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Get user from database
        user = users_model.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Verify current password
        if not verify_password(current_password, user['password_hash']):
            return jsonify({
                'success': False,
                'error': 'Invalid current password',
                'message': 'Your current password is incorrect'
            }), 400
        
        # Validate new password
        is_valid, password_message = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Invalid new password',
                'message': password_message
            }), 400
        
        # Check if new password is different from current
        if verify_password(new_password, user['password_hash']):
            return jsonify({
                'success': False,
                'error': 'Password unchanged',
                'message': 'New password must be different from current password'
            }), 400
        
        # Hash new password
        new_password_hash = hash_password(new_password)
        
        # Update password in database
        update_data = {
            'password_hash': new_password_hash,
            'updated_at': datetime.utcnow()
        }
        
        success = users_model.update_by_id(ObjectId(user_id), update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Password update failed',
                'message': 'Failed to update password in database'
            }), 500
        
        logger.info(f"Password changed for user: {request.current_user['username']}")
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        error_log_model.log_error(
            service_name="user_profile_api",
            error_type="change_password_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="high"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to change password',
            'message': 'An error occurred while changing your password'
        }), 500


# =====================================================
# ACCOUNT MANAGEMENT
# =====================================================

@bp.route('/user/activity', methods=['GET'])
@auth_required()
def get_user_activity():
    """Get user's activity summary"""
    try:
        user_id = request.current_user['id']
        
        # Get query parameters
        days = min(365, int(request.args.get('days', 30)))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user's reports
        user_reports = list(user_reports_model.find_many({
            'user_id': ObjectId(user_id),
            'created_at': {'$gte': start_date}
        }, sort=[('created_at', -1)], limit=10))
        
        # Get user's posts
        user_posts = list(posts_model.find_many({
            'user_id': ObjectId(user_id),
            'created_at': {'$gte': start_date}
        }, sort=[('created_at', -1)], limit=10))
        
        # Get activity counts
        total_reports = user_reports_model.count({'user_id': ObjectId(user_id)})
        total_posts = posts_model.count({'user_id': ObjectId(user_id)})
        recent_reports = len(user_reports)
        recent_posts = len(user_posts)
        
        # Get login sessions
        recent_sessions = list(user_sessions_model.find_many({
            'user_id': ObjectId(user_id),
            'created_at': {'$gte': start_date}
        }, sort=[('created_at', -1)], limit=5))
        
        # Format activity data
        activity = {
            'summary': {
                'total_reports': total_reports,
                'total_posts': total_posts,
                'recent_reports': recent_reports,
                'recent_posts': recent_posts,
                'recent_logins': len(recent_sessions),
                'time_period_days': days
            },
            'recent_reports': [
                {
                    'report_id': str(report['_id']),
                    'title': report.get('content', {}).get('title', ''),
                    'status': report.get('verification_status', 'pending'),
                    'created_at': report.get('created_at').isoformat() if report.get('created_at') else None
                }
                for report in user_reports
            ],
            'recent_posts': [
                {
                    'post_id': str(post['_id']),
                    'content_preview': post.get('content', '')[:100] + '...' if len(post.get('content', '')) > 100 else post.get('content', ''),
                    'post_type': post.get('post_type', 'text'),
                    'created_at': post.get('created_at').isoformat() if post.get('created_at') else None
                }
                for post in user_posts
            ],
            'recent_sessions': [
                {
                    'session_id': str(session['_id']),
                    'login_method': session.get('login_method', 'password'),
                    'created_at': session.get('created_at').isoformat() if session.get('created_at') else None,
                    'ip_address': session.get('ip_address', ''),
                    'user_agent': session.get('user_agent', '')[:50] + '...' if len(session.get('user_agent', '')) > 50 else session.get('user_agent', '')
                }
                for session in recent_sessions
            ]
        }
        
        return jsonify({
            'success': True,
            'message': 'User activity retrieved successfully',
            'data': {
                'activity': activity
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user activity error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve activity',
            'message': 'An error occurred while retrieving your activity'
        }), 500


@bp.route('/user/account', methods=['DELETE'])
@auth_required()
def delete_user_account():
    """Delete user account (simplified version)"""
    try:
        user_id = request.current_user['id']
        data = request.get_json() or {}
        
        # Require password confirmation
        if not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'Password required',
                'message': 'Password confirmation is required to delete account'
            }), 400
        
        # Get user from database
        user = users_model.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Verify password
        if not verify_password(data['password'], user['password_hash']):
            return jsonify({
                'success': False,
                'error': 'Invalid password',
                'message': 'Password is incorrect'
            }), 400
        
        # For simplified version, just deactivate the account instead of full deletion
        # In production, you might want to implement full GDPR-compliant deletion
        update_data = {
            'status': 'deleted',
            'deleted_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'deletion_reason': data.get('reason', 'user_requested')
        }
        
        success = users_model.update_by_id(ObjectId(user_id), update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Deletion failed',
                'message': 'Failed to delete account'
            }), 500
        
        # Deactivate all sessions
        user_sessions_model.update_many(
            {'user_id': ObjectId(user_id)},
            {'active': False, 'logged_out_at': datetime.utcnow()}
        )
        
        logger.info(f"Account deleted for user: {request.current_user['username']}")
        
        return jsonify({
            'success': True,
            'message': 'Account deleted successfully',
            'data': {
                'note': 'Your account has been deactivated. Contact support if you change your mind.'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Delete user account error: {e}")
        error_log_model.log_error(
            service_name="user_profile_api",
            error_type="delete_account_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="high"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to delete account',
            'message': 'An error occurred while deleting your account'
        }), 500


# =====================================================
# USER PREFERENCES & CUSTOMIZATION
# =====================================================

@bp.route('/user/preferences', methods=['GET'])
@auth_required()
def get_user_preferences():
    """Get user's UI and app preferences"""
    try:
        user_id = request.current_user['id']
        
        # Get user from database
        user = users_model.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Get or create default preferences
        preferences = user.get('preferences', {})
        
        # Default preferences if not set
        default_preferences = {
            'theme': 'light',
            'map_style': 'streets',
            'default_zoom': 10,
            'auto_location': True,
            'show_verified_only': False,
            'compact_view': False,
            'notifications_sound': True,
            'analytics_tracking': True,
            'data_usage': 'normal'  # low, normal, high
        }
        
        # Merge with defaults
        final_preferences = {**default_preferences, **preferences}
        
        return jsonify({
            'success': True,
            'message': 'Preferences retrieved successfully',
            'data': {
                'preferences': final_preferences
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user preferences error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve preferences',
            'message': 'An error occurred while retrieving your preferences'
        }), 500


@bp.route('/user/preferences', methods=['PUT'])
@auth_required()
def update_user_preferences():
    """Update user's UI and app preferences"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Validate preferences
        valid_themes = ['light', 'dark', 'auto']
        valid_map_styles = ['streets', 'satellite', 'hybrid', 'terrain']
        valid_data_usage = ['low', 'normal', 'high']
        
        preferences = {}
        
        # Theme preference
        if 'theme' in data and data['theme'] in valid_themes:
            preferences['theme'] = data['theme']
        
        # Map preferences
        if 'map_style' in data and data['map_style'] in valid_map_styles:
            preferences['map_style'] = data['map_style']
        
        if 'default_zoom' in data:
            zoom = data['default_zoom']
            if isinstance(zoom, (int, float)) and 1 <= zoom <= 20:
                preferences['default_zoom'] = zoom
        
        # Boolean preferences
        boolean_prefs = [
            'auto_location', 'show_verified_only', 'compact_view',
            'notifications_sound', 'analytics_tracking'
        ]
        
        for pref in boolean_prefs:
            if pref in data and isinstance(data[pref], bool):
                preferences[pref] = data[pref]
        
        # Data usage preference
        if 'data_usage' in data and data['data_usage'] in valid_data_usage:
            preferences['data_usage'] = data['data_usage']
        
        if not preferences:
            return jsonify({
                'success': False,
                'error': 'No valid preferences',
                'message': 'No valid preferences were provided'
            }), 400
        
        # Update user preferences
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        for key, value in preferences.items():
            update_data[f'preferences.{key}'] = value
        
        success = users_model.update_by_id(ObjectId(user_id), update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update preferences in database'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully',
            'data': {
                'updated_preferences': preferences
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update user preferences error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update preferences',
            'message': 'An error occurred while updating your preferences'
        }), 500


# =====================================================
# USER STATISTICS
# =====================================================

@bp.route('/user/statistics', methods=['GET'])
@auth_required()
def get_user_statistics():
    """Get detailed user statistics"""
    try:
        user_id = request.current_user['id']
        
        # Get time range
        days = min(365, int(request.args.get('days', 90)))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user from database
        user = users_model.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Calculate statistics
        statistics = {
            'account_info': {
                'member_since': user.get('created_at').isoformat() if user.get('created_at') else None,
                'account_age_days': (datetime.utcnow() - user.get('created_at')).days if user.get('created_at') else 0,
                'user_type': user.get('user_type_id', 'citizen'),
                'verified': user.get('verified', False),
                'status': user.get('status', 'active')
            },
            'activity_stats': {
                'total_logins': user.get('statistics', {}).get('login_count', 0),
                'last_login': user.get('last_login').isoformat() if user.get('last_login') else None,
                'total_reports': user.get('statistics', {}).get('reports_submitted', 0),
                'verified_reports': user.get('statistics', {}).get('reports_verified', 0),
                'total_posts': user.get('statistics', {}).get('posts_created', 0)
            },
            'engagement': {
                'reports_verification_rate': 0,
                'average_post_engagement': 0,
                'community_contribution_score': 0
            },
            'recent_activity': {
                'reports_last_30_days': user_reports_model.count({
                    'user_id': ObjectId(user_id),
                    'created_at': {'$gte': datetime.utcnow() - timedelta(days=30)}
                }),
                'posts_last_30_days': posts_model.count({
                    'user_id': ObjectId(user_id),
                    'created_at': {'$gte': datetime.utcnow() - timedelta(days=30)}
                }),
                'logins_last_30_days': user_sessions_model.count({
                    'user_id': ObjectId(user_id),
                    'created_at': {'$gte': datetime.utcnow() - timedelta(days=30)}
                })
            }
        }
        
        # Calculate verification rate
        total_reports = statistics['activity_stats']['total_reports']
        verified_reports = statistics['activity_stats']['verified_reports']
        if total_reports > 0:
            statistics['engagement']['reports_verification_rate'] = verified_reports / total_reports
        
        # Calculate community contribution score (simple algorithm)
        contribution_score = 0
        contribution_score += verified_reports * 10  # 10 points per verified report
        contribution_score += statistics['activity_stats']['total_posts'] * 2  # 2 points per post
        contribution_score += statistics['activity_stats']['total_logins'] * 0.1  # 0.1 points per login
        
        statistics['engagement']['community_contribution_score'] = round(contribution_score, 1)
        
        return jsonify({
            'success': True,
            'message': 'User statistics retrieved successfully',
            'data': {
                'statistics': statistics,
                'time_period_days': days,
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user statistics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': 'An error occurred while retrieving your statistics'
        }), 500


# =====================================================
# DEVELOPMENT HELPERS
# =====================================================

@bp.route('/user/dev/populate-profile', methods=['POST'])
@auth_required()
def populate_test_profile():
    """Development helper: Populate current user profile with test data"""
    try:
        # Only allow in development mode
        if not current_app.debug:
            return jsonify({
                'success': False,
                'error': 'Development only',
                'message': 'This endpoint is only available in development mode'
            }), 403
        
        user_id = request.current_user['id']
        
        # Test profile data
        test_profile_data = {
            'profile.first_name': 'Test',
            'profile.last_name': 'User',
            'profile.bio': 'This is a test user profile created for development and testing purposes. I am interested in social justice and global protest movements.',
            'profile.location': 'New York, NY, USA',
            'profile.preferred_language': 'en',
            'profile.timezone': 'America/New_York',
            'phone_number': '+1-555-0123',
            'privacy_settings.profile_public': True,
            'privacy_settings.show_activity': True,
            'privacy_settings.allow_messages': True,
            'notification_settings.email_enabled': True,
            'notification_settings.push_enabled': True,
            'notification_settings.alert_frequency': 'daily',
            'preferences.theme': 'light',
            'preferences.map_style': 'streets',
            'preferences.default_zoom': 12,
            'preferences.auto_location': True,
            'preferences.show_verified_only': False,
            'updated_at': datetime.utcnow()
        }
        
        # Update user with test data
        success = users_model.update_by_id(ObjectId(user_id), test_profile_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to populate test profile'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Test profile data populated successfully',
            'data': {
                'note': 'Profile has been populated with test data for development'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Populate test profile error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to populate test profile',
            'message': str(e)
        }), 500


# =====================================================
# HEALTH CHECK
# =====================================================

@bp.route('/user/health', methods=['GET'])
def user_profile_health_check():
    """User profile service health check"""
    try:
        # Test database connectivity
        test_count = users_model.count()
        
        return jsonify({
            'success': True,
            'message': 'User profile service is healthy',
            'data': {
                'service': 'user_profile_api',
                'status': 'healthy',
                'database_connected': True,
                'total_users': test_count,
                'features': {
                    'profile_management': True,
                    'settings_management': True,
                    'password_changes': True,
                    'activity_tracking': True,
                    'preferences': True,
                    'statistics': True,
                    'account_deletion': True
                },
                'simplified_features': {
                    'email_verification_disabled': True,
                    'password_reset_disabled': True,
                    'two_factor_auth_disabled': True
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"User profile health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'User profile service unhealthy',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['bp']