# blueprints/alerts.py
"""
Alerts Blueprint - User Notifications & Alert System
- User notification management
- Alert preferences and settings
- Notification history and read status
- Alert triggers and delivery
- In-app notification system (no email/mobile alerts)
- Simple notification tab functionality
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
import logging

# Initialize blueprint
bp = Blueprint('alerts', __name__)
logger = logging.getLogger(__name__)

# Import auth decorator
try:
    from blueprints.auth import auth_required
except ImportError:
    # Mock decorator for development
    def auth_required(allowed_roles=None):
        def decorator(f):
            def decorated_function(*args, **kwargs):
                request.current_user = {
                    'id': 'mock_user_id', 
                    'user_type': 'citizen',
                    'username': 'mockuser',
                    'email': 'mock@example.com',
                    'verified': True
                }
                return f(*args, **kwargs)
            return decorated_function
        return decorator

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.web_app_models import UserAlerts, NotificationQueue, NotificationHistory, Users
    from models.system_monitoring_models import ErrorLog
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # Mock models for development
    class UserAlerts:
        def __init__(self): pass
        def create(self, data): return ObjectId()
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
        def update_by_id(self, id, data): return True
        def delete_by_id(self, id): return True
        def count(self, query=None): return 0
    
    class NotificationQueue:
        def __init__(self): pass
        def create(self, data): return ObjectId()
        def find_many(self, query, **kwargs): return []
        def update_by_id(self, id, data): return True
        def delete_by_id(self, id): return True
        def count(self, query=None): return 0
    
    class NotificationHistory:
        def __init__(self): pass
        def create(self, data): return ObjectId()
        def find_many(self, query, **kwargs): return []
        def update_by_id(self, id, data): return True
        def count(self, query=None): return 0
    
    class Users:
        def __init__(self): pass
        def find_one(self, query): return None
        def update_by_id(self, id, data): return True
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass

# Initialize models
user_alerts_model = UserAlerts()
notification_queue_model = NotificationQueue()
notification_history_model = NotificationHistory()
users_model = Users()
error_log_model = ErrorLog()


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def format_alert(alert):
    """Format alert data for API response"""
    try:
        if not alert:
            return None
        
        formatted = {
            'alert_id': str(alert['_id']),
            'alert_name': alert.get('alert_name', ''),
            'keywords': alert.get('keywords', []),
            'categories': alert.get('categories', []),
            'countries': alert.get('countries', []),
            'cities': alert.get('cities', []),
            'alert_type': alert.get('alert_type', 'keyword'),
            'frequency': alert.get('frequency', 'daily'),
            'active': alert.get('active', True),
            'created_at': alert.get('created_at').isoformat() if alert.get('created_at') else None,
            'updated_at': alert.get('updated_at').isoformat() if alert.get('updated_at') else None,
            'last_triggered': alert.get('last_triggered').isoformat() if alert.get('last_triggered') else None,
            'trigger_count': alert.get('trigger_count', 0),
            'location_radius_km': alert.get('location_radius_km', 0),
            'coordinates': alert.get('coordinates', [])
        }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting alert: {e}")
        return None

def format_notification(notification):
    """Format notification data for API response"""
    try:
        if not notification:
            return None
        
        formatted = {
            'notification_id': str(notification['_id']),
            'title': notification.get('title', ''),
            'message': notification.get('message', ''),
            'notification_type': notification.get('notification_type', 'general'),
            'priority': notification.get('priority', 'normal'),
            'read': notification.get('read', False),
            'created_at': notification.get('created_at').isoformat() if notification.get('created_at') else None,
            'read_at': notification.get('read_at').isoformat() if notification.get('read_at') else None,
            'related_protest_id': str(notification['related_protest_id']) if notification.get('related_protest_id') else None,
            'related_alert_id': str(notification['related_alert_id']) if notification.get('related_alert_id') else None,
            'action_url': notification.get('action_url', ''),
            'metadata': notification.get('metadata', {})
        }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting notification: {e}")
        return None

def validate_alert_data(data):
    """Validate alert creation/update data"""
    errors = []
    
    # Alert name validation
    alert_name = data.get('alert_name', '').strip()
    if not alert_name:
        errors.append('Alert name is required')
    elif len(alert_name) > 100:
        errors.append('Alert name must be 100 characters or less')
    
    # Alert type validation
    alert_type = data.get('alert_type', 'keyword')
    valid_types = ['keyword', 'category', 'location', 'combined']
    if alert_type not in valid_types:
        errors.append(f'Alert type must be one of: {", ".join(valid_types)}')
    
    # Frequency validation
    frequency = data.get('frequency', 'daily')
    valid_frequencies = ['immediate', 'daily', 'weekly']
    if frequency not in valid_frequencies:
        errors.append(f'Frequency must be one of: {", ".join(valid_frequencies)}')
    
    # Keywords validation
    keywords = data.get('keywords', [])
    if alert_type in ['keyword', 'combined'] and not keywords:
        errors.append('Keywords are required for keyword-based alerts')
    
    # Categories validation
    categories = data.get('categories', [])
    if alert_type in ['category', 'combined'] and not categories:
        errors.append('Categories are required for category-based alerts')
    
    # Location validation
    if alert_type in ['location', 'combined']:
        coordinates = data.get('coordinates', [])
        if not coordinates or len(coordinates) != 2:
            errors.append('Valid coordinates are required for location-based alerts')
        else:
            try:
                lat, lng = float(coordinates[1]), float(coordinates[0])
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    errors.append('Invalid coordinate ranges')
            except (ValueError, TypeError):
                errors.append('Invalid coordinate format')
        
        radius = data.get('location_radius_km', 0)
        if radius <= 0 or radius > 1000:
            errors.append('Location radius must be between 1 and 1000 kilometers')
    
    return errors

def create_notification(user_id, title, message, notification_type='general', 
                       priority='normal', related_protest_id=None, related_alert_id=None, 
                       action_url='', metadata=None):
    """Create a new notification for a user"""
    try:
        notification_data = {
            'user_id': ObjectId(user_id),
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'priority': priority,
            'read': False,
            'created_at': datetime.utcnow(),
            'related_protest_id': ObjectId(related_protest_id) if related_protest_id else None,
            'related_alert_id': ObjectId(related_alert_id) if related_alert_id else None,
            'action_url': action_url,
            'metadata': metadata or {}
        }
        
        # Add to notification history
        notification_id = notification_history_model.create(notification_data)
        
        # Also add to notification queue for delivery
        queue_data = {
            'user_id': ObjectId(user_id),
            'notification_id': notification_id,
            'status': 'delivered',  # Since we're doing in-app only
            'delivery_method': 'in_app',
            'created_at': datetime.utcnow(),
            'delivered_at': datetime.utcnow()
        }
        notification_queue_model.create(queue_data)
        
        return notification_id
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return None


# =====================================================
# USER ALERTS ENDPOINTS
# =====================================================

@bp.route('/alerts', methods=['POST'])
@auth_required()
def create_alert():
    """Create a new alert"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Validate alert data
        validation_errors = validate_alert_data(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'message': 'Alert validation failed',
                'details': validation_errors
            }), 400
        
        # Check user's alert limit
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        user_type = user.get('user_type_id', 'citizen')
        alert_limits = {
            'citizen': 5,
            'activist': 15,
            'journalist': 25,
            'researcher': 20,
            'ngo_worker': 30,
            'moderator': 50,
            'admin': -1  # Unlimited
        }
        
        max_alerts = alert_limits.get(user_type, 5)
        current_alerts = user_alerts_model.count({'user_id': ObjectId(user_id), 'active': True})
        
        if max_alerts != -1 and current_alerts >= max_alerts:
            return jsonify({
                'success': False,
                'error': 'Alert limit reached',
                'message': f'You have reached your limit of {max_alerts} active alerts'
            }), 400
        
        # Create alert
        alert_data = {
            'user_id': ObjectId(user_id),
            'alert_name': data['alert_name'].strip(),
            'keywords': [kw.strip().lower() for kw in data.get('keywords', [])],
            'categories': [cat.strip() for cat in data.get('categories', [])],
            'countries': [country.strip() for country in data.get('countries', [])],
            'cities': [city.strip() for city in data.get('cities', [])],
            'alert_type': data.get('alert_type', 'keyword'),
            'frequency': data.get('frequency', 'daily'),
            'active': data.get('active', True),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_triggered': None,
            'trigger_count': 0,
            'coordinates': data.get('coordinates', []),
            'location_radius_km': data.get('location_radius_km', 0),
            'metadata': {
                'created_by_ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
        }
        
        alert_id = user_alerts_model.create(alert_data)
        
        # Create welcome notification
        create_notification(
            user_id=user_id,
            title='Alert Created',
            message=f'Your alert "{data["alert_name"]}" has been created successfully.',
            notification_type='alert_created',
            related_alert_id=alert_id
        )
        
        # Get created alert
        created_alert = user_alerts_model.find_one({'_id': alert_id})
        formatted_alert = format_alert(created_alert)
        
        logger.info(f"Alert created by user {request.current_user['username']}: {data['alert_name']}")
        
        return jsonify({
            'success': True,
            'message': 'Alert created successfully',
            'data': {
                'alert': formatted_alert
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Create alert error: {e}")
        error_log_model.log_error(
            service_name="alerts_api",
            error_type="create_alert_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to create alert',
            'message': 'An error occurred while creating your alert'
        }), 500


@bp.route('/alerts', methods=['GET'])
@auth_required()
def get_user_alerts():
    """Get user's alerts"""
    try:
        user_id = request.current_user['id']
        
        # Parse filters
        filters = {'user_id': ObjectId(user_id)}
        
        # Filter by active status
        if request.args.get('active') == 'true':
            filters['active'] = True
        elif request.args.get('active') == 'false':
            filters['active'] = False
        
        # Filter by alert type
        alert_type = request.args.get('type')
        if alert_type:
            filters['alert_type'] = alert_type
        
        # Get alerts
        alerts = list(user_alerts_model.find_many(
            filters,
            sort=[('created_at', -1)]
        ))
        
        # Format alerts
        formatted_alerts = []
        for alert in alerts:
            formatted_alert = format_alert(alert)
            if formatted_alert:
                formatted_alerts.append(formatted_alert)
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_alerts)} alerts',
            'data': {
                'alerts': formatted_alerts,
                'total_count': len(formatted_alerts),
                'active_count': len([a for a in formatted_alerts if a['active']]),
                'inactive_count': len([a for a in formatted_alerts if not a['active']])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user alerts error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve alerts',
            'message': 'An error occurred while retrieving your alerts'
        }), 500


@bp.route('/alerts/<alert_id>', methods=['GET'])
@auth_required()
def get_alert_details(alert_id):
    """Get detailed information about a specific alert"""
    try:
        # Validate alert ID
        if not ObjectId.is_valid(alert_id):
            return jsonify({
                'success': False,
                'error': 'Invalid alert ID',
                'message': 'The provided alert ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        
        # Get alert
        alert = user_alerts_model.find_one({
            '_id': ObjectId(alert_id),
            'user_id': ObjectId(user_id)
        })
        
        if not alert:
            return jsonify({
                'success': False,
                'error': 'Alert not found',
                'message': 'The requested alert could not be found'
            }), 404
        
        # Format alert
        formatted_alert = format_alert(alert)
        
        # Get recent notifications for this alert
        recent_notifications = list(notification_history_model.find_many({
            'user_id': ObjectId(user_id),
            'related_alert_id': ObjectId(alert_id)
        }, sort=[('created_at', -1)], limit=10))
        
        formatted_notifications = []
        for notification in recent_notifications:
            formatted_notification = format_notification(notification)
            if formatted_notification:
                formatted_notifications.append(formatted_notification)
        
        return jsonify({
            'success': True,
            'message': 'Alert details retrieved successfully',
            'data': {
                'alert': formatted_alert,
                'recent_notifications': formatted_notifications,
                'notification_count': len(formatted_notifications)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get alert details error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve alert details',
            'message': 'An error occurred while retrieving alert details'
        }), 500


@bp.route('/alerts/<alert_id>', methods=['PUT'])
@auth_required()
def update_alert(alert_id):
    """Update an alert"""
    try:
        # Validate alert ID
        if not ObjectId.is_valid(alert_id):
            return jsonify({
                'success': False,
                'error': 'Invalid alert ID',
                'message': 'The provided alert ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Get alert
        alert = user_alerts_model.find_one({
            '_id': ObjectId(alert_id),
            'user_id': ObjectId(user_id)
        })
        
        if not alert:
            return jsonify({
                'success': False,
                'error': 'Alert not found',
                'message': 'The requested alert could not be found'
            }), 404
        
        # Validate update data
        validation_errors = validate_alert_data(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'message': 'Alert validation failed',
                'details': validation_errors
            }), 400
        
        # Build update data
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        # Update fields
        updateable_fields = [
            'alert_name', 'keywords', 'categories', 'countries', 'cities',
            'alert_type', 'frequency', 'active', 'coordinates', 'location_radius_km'
        ]
        
        for field in updateable_fields:
            if field in data:
                if field in ['keywords', 'categories', 'countries', 'cities']:
                    update_data[field] = [item.strip().lower() if field == 'keywords' else item.strip() 
                                        for item in data[field]]
                elif field == 'alert_name':
                    update_data[field] = data[field].strip()
                else:
                    update_data[field] = data[field]
        
        # Update alert
        success = user_alerts_model.update_by_id(ObjectId(alert_id), update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update alert in database'
            }), 500
        
        # Get updated alert
        updated_alert = user_alerts_model.find_one({'_id': ObjectId(alert_id)})
        formatted_alert = format_alert(updated_alert)
        
        logger.info(f"Alert updated by user {request.current_user['username']}: {alert_id}")
        
        return jsonify({
            'success': True,
            'message': 'Alert updated successfully',
            'data': {
                'alert': formatted_alert
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update alert error: {e}")
        error_log_model.log_error(
            service_name="alerts_api",
            error_type="update_alert_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            context={'alert_id': alert_id},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to update alert',
            'message': 'An error occurred while updating your alert'
        }), 500


@bp.route('/alerts/<alert_id>', methods=['DELETE'])
@auth_required()
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        # Validate alert ID
        if not ObjectId.is_valid(alert_id):
            return jsonify({
                'success': False,
                'error': 'Invalid alert ID',
                'message': 'The provided alert ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        
        # Get alert
        alert = user_alerts_model.find_one({
            '_id': ObjectId(alert_id),
            'user_id': ObjectId(user_id)
        })
        
        if not alert:
            return jsonify({
                'success': False,
                'error': 'Alert not found',
                'message': 'The requested alert could not be found'
            }), 404
        
        # Delete alert
        success = user_alerts_model.delete_by_id(ObjectId(alert_id))
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Deletion failed',
                'message': 'Failed to delete alert from database'
            }), 500
        
        logger.info(f"Alert deleted by user {request.current_user['username']}: {alert_id}")
        
        return jsonify({
            'success': True,
            'message': 'Alert deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete alert error: {e}")
        error_log_model.log_error(
            service_name="alerts_api",
            error_type="delete_alert_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            context={'alert_id': alert_id},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to delete alert',
            'message': 'An error occurred while deleting your alert'
        }), 500


# =====================================================
# NOTIFICATIONS ENDPOINTS
# =====================================================

@bp.route('/notifications', methods=['GET'])
@auth_required()
def get_user_notifications():
    """Get user's notifications"""
    try:
        user_id = request.current_user['id']
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(100, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Parse filters
        filters = {'user_id': ObjectId(user_id)}
        
        # Filter by read status
        if request.args.get('unread_only') == 'true':
            filters['read'] = False
        elif request.args.get('read_only') == 'true':
            filters['read'] = True
        
        # Filter by notification type
        notification_type = request.args.get('type')
        if notification_type:
            filters['notification_type'] = notification_type
        
        # Filter by priority
        priority = request.args.get('priority')
        if priority:
            filters['priority'] = priority
        
        # Get notifications
        notifications = list(notification_history_model.find_many(
            filters,
            sort=[('created_at', -1)],
            limit=limit,
            skip=offset
        ))
        
        # Get total count
        total_count = notification_history_model.count(filters)
        
        # Format notifications
        formatted_notifications = []
        for notification in notifications:
            formatted_notification = format_notification(notification)
            if formatted_notification:
                formatted_notifications.append(formatted_notification)
        
        # Pagination info
        total_pages = (total_count + limit - 1) // limit
        
        # Get unread count for user
        unread_count = notification_history_model.count({
            'user_id': ObjectId(user_id),
            'read': False
        })
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_notifications)} notifications',
            'data': {
                'notifications': formatted_notifications,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'summary': {
                    'unread_count': unread_count,
                    'total_notifications': total_count
                },
                'filters_applied': {
                    'unread_only': request.args.get('unread_only') == 'true',
                    'type': notification_type,
                    'priority': priority
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user notifications error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve notifications',
            'message': 'An error occurred while retrieving your notifications'
        }), 500


@bp.route('/notifications/<notification_id>/read', methods=['PUT'])
@auth_required()
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        # Validate notification ID
        if not ObjectId.is_valid(notification_id):
            return jsonify({
                'success': False,
                'error': 'Invalid notification ID',
                'message': 'The provided notification ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        
        # Get notification
        notification = notification_history_model.find_one({
            '_id': ObjectId(notification_id),
            'user_id': ObjectId(user_id)
        })
        
        if not notification:
            return jsonify({
                'success': False,
                'error': 'Notification not found',
                'message': 'The requested notification could not be found'
            }), 404
        
        # Mark as read
        success = notification_history_model.update_by_id(ObjectId(notification_id), {
            'read': True,
            'read_at': datetime.utcnow()
        })
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to mark notification as read'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        }), 200
        
    except Exception as e:
        logger.error(f"Mark notification read error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark notification as read',
            'message': 'An error occurred while updating the notification'
        }), 500


@bp.route('/notifications/read-all', methods=['PUT'])
@auth_required()
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        user_id = request.current_user['id']
        
        # Mark all unread notifications as read
        result = notification_history_model.update_many(
            {
                'user_id': ObjectId(user_id),
                'read': False
            },
            {
                'read': True,
                'read_at': datetime.utcnow()
            }
        )
        
        marked_count = getattr(result, 'modified_count', 0)
        
        return jsonify({
            'success': True,
            'message': f'Marked {marked_count} notifications as read',
            'data': {
                'marked_count': marked_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Mark all notifications read error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark notifications as read',
            'message': 'An error occurred while updating notifications'
        }), 500


@bp.route('/notifications/unread-count', methods=['GET'])
@auth_required()
def get_unread_count():
    """Get count of unread notifications"""
    try:
        user_id = request.current_user['id']
        
        unread_count = notification_history_model.count({
            'user_id': ObjectId(user_id),
            'read': False
        })
        
        return jsonify({
            'success': True,
            'message': 'Unread count retrieved successfully',
            'data': {
                'unread_count': unread_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get unread count error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get unread count',
            'message': 'An error occurred while retrieving unread count'
        }), 500


# =====================================================
# TESTING ENDPOINTS (Development)
# =====================================================

@bp.route('/notifications/test', methods=['POST'])
@auth_required()
def create_test_notification():
    """Create a test notification (development only)"""
    try:
        # Only allow in development mode
        if not current_app.debug:
            return jsonify({
                'success': False,
                'error': 'Development only',
                'message': 'This endpoint is only available in development mode'
            }), 403
        
        user_id = request.current_user['id']
        data = request.get_json() or {}
        
        # Create test notification
        notification_id = create_notification(
            user_id=user_id,
            title=data.get('title', 'Test Notification'),
            message=data.get('message', 'This is a test notification created for development testing.'),
            notification_type=data.get('type', 'test'),
            priority=data.get('priority', 'normal')
        )
        
        if not notification_id:
            return jsonify({
                'success': False,
                'error': 'Creation failed',
                'message': 'Failed to create test notification'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Test notification created successfully',
            'data': {
                'notification_id': str(notification_id)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Create test notification error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create test notification',
            'message': str(e)
        }), 500


# =====================================================
# ALERT STATISTICS
# =====================================================

@bp.route('/alerts/statistics', methods=['GET'])
@auth_required()
def get_alerts_statistics():
    """Get user's alert statistics"""
    try:
        user_id = request.current_user['id']
        
        # Get basic statistics
        stats = {
            'total_alerts': user_alerts_model.count({'user_id': ObjectId(user_id)}),
            'active_alerts': user_alerts_model.count({
                'user_id': ObjectId(user_id),
                'active': True
            }),
            'inactive_alerts': user_alerts_model.count({
                'user_id': ObjectId(user_id),
                'active': False
            })
        }
        
        # Get alerts by type
        alert_types = {}
        try:
            pipeline = [
                {'$match': {'user_id': ObjectId(user_id)}},
                {'$group': {'_id': '$alert_type', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            
            type_results = list(user_alerts_model.collection.aggregate(pipeline))
            for result in type_results:
                alert_types[result['_id']] = result['count']
        except Exception:
            alert_types = {}
        
        # Get notifications statistics
        notification_stats = {
            'total_notifications': notification_history_model.count({
                'user_id': ObjectId(user_id)
            }),
            'unread_notifications': notification_history_model.count({
                'user_id': ObjectId(user_id),
                'read': False
            }),
            'recent_notifications': notification_history_model.count({
                'user_id': ObjectId(user_id),
                'created_at': {'$gte': datetime.utcnow() - timedelta(days=7)}
            })
        }
        
        # Calculate engagement score
        engagement_score = (
            stats['active_alerts'] * 5 +
            notification_stats['total_notifications'] * 0.5
        )
        
        return jsonify({
            'success': True,
            'message': 'Alert statistics retrieved successfully',
            'data': {
                'alert_statistics': stats,
                'alert_types_distribution': alert_types,
                'notification_statistics': notification_stats,
                'engagement': {
                    'score': round(engagement_score, 1),
                    'level': 'high' if engagement_score > 50 else 'medium' if engagement_score > 10 else 'low'
                },
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get alerts statistics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': 'An error occurred while retrieving alert statistics'
        }), 500


# =====================================================
# HEALTH CHECK
# =====================================================

@bp.route('/alerts/health', methods=['GET'])
def alerts_health_check():
    """Alerts service health check"""
    try:
        # Test database connectivity
        alerts_count = user_alerts_model.count()
        notifications_count = notification_history_model.count()
        
        return jsonify({
            'success': True,
            'message': 'Alerts service is healthy',
            'data': {
                'service': 'alerts_api',
                'status': 'healthy',
                'database_connected': True,
                'total_alerts': alerts_count,
                'total_notifications': notifications_count,
                'features': {
                    'alert_management': True,
                    'in_app_notifications': True,
                    'notification_history': True,
                    'alert_statistics': True,
                    'bulk_operations': True,
                    'real_time_alerts': False  # Would require background processing
                },
                'alert_types_supported': [
                    'keyword', 'category', 'location', 'combined'
                ],
                'notification_delivery': [
                    'in_app'  # Only in-app for simplified version
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Alerts health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Alerts service unhealthy',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['bp']