# blueprints/user_content.py
"""
User Content Blueprint - User-Generated Content Management
- User protest reports with media uploads
- User posts and social content
- Content moderation and verification
- Media file handling
- Content editing and deletion
- Simplified version without complex approval workflows
"""

import os
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
import logging
import re

# Initialize blueprint
bp = Blueprint('user_content', __name__)
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
    from models.web_app_models import UserReports, Posts, Users
    from models.data_collection_models import Protest
    from models.system_monitoring_models import ErrorLog
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # Mock models for development
    class UserReports:
        def __init__(self): pass
        def create(self, data): return ObjectId()
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
        def update_by_id(self, id, data): return True
        def delete_by_id(self, id): return True
        def count(self, query=None): return 0
    
    class Posts:
        def __init__(self): pass
        def create(self, data): return ObjectId()
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
        def update_by_id(self, id, data): return True
        def delete_by_id(self, id): return True
        def count(self, query=None): return 0
    
    class Users:
        def __init__(self): pass
        def find_one(self, query): return None
        def update_by_id(self, id, data): return True
    
    class Protest:
        def __init__(self): pass
        def find_one(self, query): return None
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass

# Initialize models
user_reports_model = UserReports()
posts_model = Posts()
users_model = Users()
protest_model = Protest()
error_log_model = ErrorLog()


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def validate_content_data(data, content_type='report'):
    """Validate user content data"""
    errors = []
    
    if content_type == 'report':
        # Title validation
        title = data.get('title', '').strip()
        if not title:
            errors.append('Title is required')
        elif len(title) < 10:
            errors.append('Title must be at least 10 characters long')
        elif len(title) > 200:
            errors.append('Title must be 200 characters or less')
        
        # Description validation
        description = data.get('description', '').strip()
        if not description:
            errors.append('Description is required')
        elif len(description) < 20:
            errors.append('Description must be at least 20 characters long')
        elif len(description) > 2000:
            errors.append('Description must be 2000 characters or less')
        
        # Location validation
        location = data.get('location', '').strip()
        if not location:
            errors.append('Location is required')
        elif len(location) > 200:
            errors.append('Location must be 200 characters or less')
    
    elif content_type == 'post':
        # Content validation
        content = data.get('content', '').strip()
        if not content:
            errors.append('Post content is required')
        elif len(content) > 1000:
            errors.append('Post content must be 1000 characters or less')
    
    return errors

def validate_coordinates(lat, lng):
    """Validate geographic coordinates"""
    try:
        lat = float(lat)
        lng = float(lng)
        
        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"
        
        if not (-180 <= lng <= 180):
            return False, "Longitude must be between -180 and 180"
        
        return True, None
        
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"

def format_user_report(report, include_sensitive=False):
    """Format user report for API response"""
    try:
        if not report:
            return None
        
        formatted = {
            'id': str(report['_id']),
            'title': report.get('content', {}).get('title', ''),
            'description': report.get('content', {}).get('description', ''),
            'location': {
                'description': report.get('content', {}).get('location', ''),
                'coordinates': report.get('location', {}).get('coordinates', [0, 0])
            },
            'tags': report.get('tags', []),
            'verification_status': report.get('verification_status', 'pending'),
            'priority_level': report.get('priority_level', 'normal'),
            'credibility_score': report.get('credibility_score', 0),
            'created_at': report.get('created_at').isoformat() if report.get('created_at') else None,
            'updated_at': report.get('updated_at').isoformat() if report.get('updated_at') else None,
            'media_files': [
                {
                    'file_id': str(media.get('file_id', '')),
                    'file_type': media.get('file_type', ''),
                    'file_name': media.get('file_name', ''),
                    'file_size': media.get('file_size', 0),
                    'uploaded_at': media.get('uploaded_at').isoformat() if media.get('uploaded_at') else None
                }
                for media in report.get('media_files', [])
            ]
        }
        
        # Include sensitive data for authorized users
        if include_sensitive:
            formatted['internal'] = {
                'user_id': str(report.get('user_id', '')),
                'auto_moderation_score': report.get('auto_moderation_score', 0),
                'escalated': report.get('escalated', False),
                'ip_address': report.get('metadata', {}).get('ip_address', ''),
                'user_agent': report.get('metadata', {}).get('user_agent', '')
            }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting user report: {e}")
        return None

def format_user_post(post, include_sensitive=False):
    """Format user post for API response"""
    try:
        if not post:
            return None
        
        formatted = {
            'id': str(post['_id']),
            'content': post.get('content', ''),
            'post_type': post.get('post_type', 'text'),
            'hashtags': post.get('hashtags', []),
            'visibility': post.get('visibility', 'public'),
            'moderation_status': post.get('moderation_status', 'approved'),
            'created_at': post.get('created_at').isoformat() if post.get('created_at') else None,
            'updated_at': post.get('updated_at').isoformat() if post.get('updated_at') else None,
            'engagement': {
                'likes': post.get('engagement', {}).get('likes', 0),
                'shares': post.get('engagement', {}).get('shares', 0),
                'comments': post.get('engagement', {}).get('comments', 0)
            },
            'related_protest_id': str(post['protest_id']) if post.get('protest_id') else None
        }
        
        # Include sensitive data for authorized users
        if include_sensitive:
            formatted['internal'] = {
                'user_id': str(post.get('user_id', '')),
                'ip_address': post.get('metadata', {}).get('ip_address', ''),
                'flagged_count': post.get('flagged_count', 0)
            }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting user post: {e}")
        return None

def extract_hashtags(content):
    """Extract hashtags from content"""
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, content)
    return [tag.lower() for tag in hashtags]

def calculate_credibility_score(user_type, account_age_days, previous_reports_verified):
    """Calculate basic credibility score for user report"""
    score = 0.5  # Base score
    
    # User type bonus
    type_bonus = {
        'journalist': 0.3,
        'ngo_worker': 0.25,
        'activist': 0.15,
        'researcher': 0.2,
        'citizen': 0.1
    }
    score += type_bonus.get(user_type, 0)
    
    # Account age bonus (max 0.1)
    if account_age_days > 365:
        score += 0.1
    elif account_age_days > 90:
        score += 0.05
    
    # Previous verification history (max 0.1)
    if previous_reports_verified > 10:
        score += 0.1
    elif previous_reports_verified > 5:
        score += 0.05
    
    return min(1.0, score)


# =====================================================
# USER REPORTS ENDPOINTS
# =====================================================

@bp.route('/reports', methods=['POST'])
@auth_required()
def submit_protest_report():
    """Submit a new protest report"""
    try:
        user_id = request.current_user['id']
        user_type = request.current_user['user_type']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Validate content data
        validation_errors = validate_content_data(data, 'report')
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'message': 'Report validation failed',
                'details': validation_errors
            }), 400
        
        # Validate coordinates if provided
        lat = data.get('latitude')
        lng = data.get('longitude')
        coordinates = [0, 0]  # Default
        
        if lat is not None and lng is not None:
            coords_valid, coords_error = validate_coordinates(lat, lng)
            if not coords_valid:
                return jsonify({
                    'success': False,
                    'error': 'Invalid coordinates',
                    'message': coords_error
                }), 400
            coordinates = [float(lng), float(lat)]  # GeoJSON format: [lng, lat]
        
        # Get user info for credibility scoring
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Calculate account age
        account_age = (datetime.utcnow() - user.get('created_at')).days if user.get('created_at') else 0
        previous_verified = user.get('statistics', {}).get('reports_verified', 0)
        
        # Calculate credibility score
        credibility_score = calculate_credibility_score(user_type, account_age, previous_verified)
        
        # Determine priority level
        priority_level = 'high' if credibility_score > 0.8 else 'normal' if credibility_score > 0.5 else 'low'
        
        # Create report data
        report_data = {
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(data['protest_id']) if data.get('protest_id') else None,
            'content': {
                'title': data['title'].strip(),
                'description': data['description'].strip(),
                'location': data['location'].strip()
            },
            'location': {
                'type': 'Point',
                'coordinates': coordinates
            },
            'tags': [tag.strip().lower() for tag in data.get('tags', [])],
            'verification_status': 'pending',
            'priority_level': priority_level,
            'credibility_score': credibility_score,
            'escalated': False,
            'auto_moderation_score': 0.5,  # TODO: Implement auto-moderation
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'metadata': {
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'submission_method': 'web_form'
            },
            'media_files': []  # Will be populated when media is uploaded
        }
        
        # Create report
        report_id = user_reports_model.create(report_data)
        
        # Update user statistics
        users_model.update_by_id(ObjectId(user_id), {
            'statistics.reports_submitted': user.get('statistics', {}).get('reports_submitted', 0) + 1,
            'statistics.last_active': datetime.utcnow()
        })
        
        # Format response
        created_report = user_reports_model.find_one({'_id': report_id})
        formatted_report = format_user_report(created_report)
        
        logger.info(f"Report submitted by user {request.current_user['username']}: {data['title']}")
        
        return jsonify({
            'success': True,
            'message': 'Report submitted successfully',
            'data': {
                'report': formatted_report,
                'estimated_review_time': '24-48 hours',
                'submission_id': str(report_id)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Submit report error: {e}")
        error_log_model.log_error(
            service_name="user_content_api",
            error_type="submit_report_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to submit report',
            'message': 'An error occurred while submitting your report'
        }), 500


@bp.route('/reports/my-reports', methods=['GET'])
@auth_required()
def get_user_reports():
    """Get current user's submitted reports"""
    try:
        user_id = request.current_user['id']
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 10))))
        offset = (page - 1) * limit
        
        # Parse filters
        status_filter = request.args.get('status')
        filters = {'user_id': ObjectId(user_id)}
        
        if status_filter:
            filters['verification_status'] = status_filter
        
        # Get user's reports
        reports = list(user_reports_model.find_many(
            filters,
            sort=[('created_at', -1)],
            limit=limit,
            skip=offset
        ))
        
        # Get total count
        total_count = user_reports_model.count(filters)
        
        # Format reports
        formatted_reports = []
        for report in reports:
            formatted_report = format_user_report(report, include_sensitive=True)
            if formatted_report:
                formatted_reports.append(formatted_report)
        
        # Pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_reports)} reports',
            'data': {
                'reports': formatted_reports,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user reports error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve reports',
            'message': 'An error occurred while retrieving your reports'
        }), 500


@bp.route('/reports/<report_id>', methods=['GET'])
@auth_required()
def get_report_details(report_id):
    """Get detailed information about a specific report"""
    try:
        # Validate report ID
        if not ObjectId.is_valid(report_id):
            return jsonify({
                'success': False,
                'error': 'Invalid report ID',
                'message': 'The provided report ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        user_type = request.current_user['user_type']
        
        # Get report
        report = user_reports_model.find_one({'_id': ObjectId(report_id)})
        
        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found',
                'message': 'The requested report could not be found'
            }), 404
        
        # Check permissions (user can view their own reports, admins/moderators can view all)
        can_view = (
            str(report['user_id']) == str(user_id) or 
            user_type in ['admin', 'moderator']
        )
        
        if not can_view:
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You do not have permission to view this report'
            }), 403
        
        # Format report with appropriate level of detail
        include_sensitive = user_type in ['admin', 'moderator']
        formatted_report = format_user_report(report, include_sensitive=include_sensitive)
        
        return jsonify({
            'success': True,
            'message': 'Report details retrieved successfully',
            'data': {
                'report': formatted_report
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get report details error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve report details',
            'message': 'An error occurred while retrieving report details'
        }), 500


@bp.route('/reports/<report_id>', methods=['PUT'])
@auth_required()
def update_user_report(report_id):
    """Update a user's report (only if not yet verified)"""
    try:
        # Validate report ID
        if not ObjectId.is_valid(report_id):
            return jsonify({
                'success': False,
                'error': 'Invalid report ID',
                'message': 'The provided report ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Get report
        report = user_reports_model.find_one({'_id': ObjectId(report_id)})
        
        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found',
                'message': 'The requested report could not be found'
            }), 404
        
        # Check if user owns the report
        if str(report['user_id']) != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You can only edit your own reports'
            }), 403
        
        # Check if report can be edited (not verified yet)
        if report.get('verification_status') in ['verified', 'rejected']:
            return jsonify({
                'success': False,
                'error': 'Report cannot be edited',
                'message': 'This report has already been reviewed and cannot be edited'
            }), 400
        
        # Validate update data
        validation_errors = validate_content_data(data, 'report')
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'message': 'Report validation failed',
                'details': validation_errors
            }), 400
        
        # Build update data
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        # Update content fields
        if 'title' in data:
            update_data['content.title'] = data['title'].strip()
        
        if 'description' in data:
            update_data['content.description'] = data['description'].strip()
        
        if 'location' in data:
            update_data['content.location'] = data['location'].strip()
        
        if 'tags' in data:
            update_data['tags'] = [tag.strip().lower() for tag in data['tags']]
        
        # Update coordinates if provided
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        if lat is not None and lng is not None:
            coords_valid, coords_error = validate_coordinates(lat, lng)
            if not coords_valid:
                return jsonify({
                    'success': False,
                    'error': 'Invalid coordinates',
                    'message': coords_error
                }), 400
            update_data['location.coordinates'] = [float(lng), float(lat)]
        
        # Update report
        success = user_reports_model.update_by_id(ObjectId(report_id), update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update report in database'
            }), 500
        
        # Get updated report
        updated_report = user_reports_model.find_one({'_id': ObjectId(report_id)})
        formatted_report = format_user_report(updated_report)
        
        logger.info(f"Report updated by user {request.current_user['username']}: {report_id}")
        
        return jsonify({
            'success': True,
            'message': 'Report updated successfully',
            'data': {
                'report': formatted_report
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update report error: {e}")
        error_log_model.log_error(
            service_name="user_content_api",
            error_type="update_report_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            context={'report_id': report_id},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to update report',
            'message': 'An error occurred while updating your report'
        }), 500


@bp.route('/reports/<report_id>', methods=['DELETE'])
@auth_required()
def delete_user_report(report_id):
    """Delete a user's report (only if not yet verified)"""
    try:
        # Validate report ID
        if not ObjectId.is_valid(report_id):
            return jsonify({
                'success': False,
                'error': 'Invalid report ID',
                'message': 'The provided report ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        
        # Get report
        report = user_reports_model.find_one({'_id': ObjectId(report_id)})
        
        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found',
                'message': 'The requested report could not be found'
            }), 404
        
        # Check if user owns the report
        if str(report['user_id']) != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You can only delete your own reports'
            }), 403
        
        # Check if report can be deleted (not verified yet)
        if report.get('verification_status') == 'verified':
            return jsonify({
                'success': False,
                'error': 'Report cannot be deleted',
                'message': 'Verified reports cannot be deleted'
            }), 400
        
        # Delete report
        success = user_reports_model.delete_by_id(ObjectId(report_id))
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Deletion failed',
                'message': 'Failed to delete report from database'
            }), 500
        
        # Update user statistics
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if user:
            current_count = user.get('statistics', {}).get('reports_submitted', 0)
            users_model.update_by_id(ObjectId(user_id), {
                'statistics.reports_submitted': max(0, current_count - 1)
            })
        
        logger.info(f"Report deleted by user {request.current_user['username']}: {report_id}")
        
        return jsonify({
            'success': True,
            'message': 'Report deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete report error: {e}")
        error_log_model.log_error(
            service_name="user_content_api",
            error_type="delete_report_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            context={'report_id': report_id},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to delete report',
            'message': 'An error occurred while deleting your report'
        }), 500


# =====================================================
# USER POSTS ENDPOINTS
# =====================================================

@bp.route('/posts', methods=['POST'])
@auth_required()
def create_user_post():
    """Create a new user post"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Validate content data
        validation_errors = validate_content_data(data, 'post')
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'message': 'Post validation failed',
                'details': validation_errors
            }), 400
        
        # Extract hashtags from content
        content = data['content'].strip()
        hashtags = extract_hashtags(content)
        
        # Validate protest ID if provided
        protest_id = None
        if data.get('protest_id'):
            if not ObjectId.is_valid(data['protest_id']):
                return jsonify({
                    'success': False,
                    'error': 'Invalid protest ID',
                    'message': 'The provided protest ID is not valid'
                }), 400
            
            # Check if protest exists
            protest = protest_model.find_one({'_id': ObjectId(data['protest_id'])})
            if not protest:
                return jsonify({
                    'success': False,
                    'error': 'Protest not found',
                    'message': 'The specified protest could not be found'
                }), 404
            
            protest_id = ObjectId(data['protest_id'])
        
        # Create post data
        post_data = {
            'user_id': ObjectId(user_id),
            'protest_id': protest_id,
            'content': content,
            'post_type': data.get('post_type', 'text'),
            'hashtags': hashtags,
            'visibility': data.get('visibility', 'public'),
            'moderation_status': 'approved',  # Auto-approve for simplicity
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'engagement': {
                'likes': 0,
                'shares': 0,
                'comments': 0
            },
            'flagged_count': 0,
            'metadata': {
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'creation_method': 'web_form'
            }
        }
        
        # Create post
        post_id = posts_model.create(post_data)
        
        # Update user statistics
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if user:
            users_model.update_by_id(ObjectId(user_id), {
                'statistics.posts_created': user.get('statistics', {}).get('posts_created', 0) + 1,
                'statistics.last_active': datetime.utcnow()
            })
        
        # Format response
        created_post = posts_model.find_one({'_id': post_id})
        formatted_post = format_user_post(created_post)
        
        logger.info(f"Post created by user {request.current_user['username']}: {post_id}")
        
        return jsonify({
            'success': True,
            'message': 'Post created successfully',
            'data': {
                'post': formatted_post
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Create post error: {e}")
        error_log_model.log_error(
            service_name="user_content_api",
            error_type="create_post_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to create post',
            'message': 'An error occurred while creating your post'
        }), 500


@bp.route('/posts', methods=['GET'])
def get_posts_feed():
    """Get posts feed (public posts or user's posts if authenticated)"""
    try:
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Parse filters
        filters = {'visibility': 'public', 'moderation_status': 'approved'}
        
        # Filter by protest if specified
        protest_id = request.args.get('protest_id')
        if protest_id and ObjectId.is_valid(protest_id):
            filters['protest_id'] = ObjectId(protest_id)
        
        # Filter by hashtag
        hashtag = request.args.get('hashtag')
        if hashtag:
            filters['hashtags'] = hashtag.lower()
        
        # If user is authenticated, they can see their own posts regardless of visibility
        user_id = None
        if hasattr(request, 'current_user'):
            user_id = request.current_user.get('id')
            
            # Show user's own posts if requested
            if request.args.get('my_posts') == 'true':
                filters = {'user_id': ObjectId(user_id)}
        
        # Get posts
        posts = list(posts_model.find_many(
            filters,
            sort=[('created_at', -1)],
            limit=limit,
            skip=offset
        ))
        
        # Get total count
        total_count = posts_model.count(filters)
        
        # Format posts
        formatted_posts = []
        for post in posts:
            include_sensitive = (
                user_id and 
                (str(post.get('user_id')) == str(user_id) or 
                 getattr(request, 'current_user', {}).get('user_type') in ['admin', 'moderator'])
            )
            formatted_post = format_user_post(post, include_sensitive=include_sensitive)
            if formatted_post:
                formatted_posts.append(formatted_post)
        
        # Pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_posts)} posts',
            'data': {
                'posts': formatted_posts,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'filters_applied': {
                    'protest_id': protest_id,
                    'hashtag': hashtag,
                    'my_posts_only': request.args.get('my_posts') == 'true'
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get posts feed error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve posts',
            'message': 'An error occurred while retrieving posts'
        }), 500


@bp.route('/posts/<post_id>', methods=['GET'])
def get_post_details(post_id):
    """Get detailed information about a specific post"""
    try:
        # Validate post ID
        if not ObjectId.is_valid(post_id):
            return jsonify({
                'success': False,
                'error': 'Invalid post ID',
                'message': 'The provided post ID is not valid'
            }), 400
        
        # Get post
        post = posts_model.find_one({'_id': ObjectId(post_id)})
        
        if not post:
            return jsonify({
                'success': False,
                'error': 'Post not found',
                'message': 'The requested post could not be found'
            }), 404
        
        # Check visibility
        user_id = getattr(request, 'current_user', {}).get('id')
        user_type = getattr(request, 'current_user', {}).get('user_type')
        
        # Post must be public or user must own it or be admin/moderator
        can_view = (
            post.get('visibility') == 'public' or
            (user_id and str(post.get('user_id')) == str(user_id)) or
            user_type in ['admin', 'moderator']
        )
        
        if not can_view:
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You do not have permission to view this post'
            }), 403
        
        # Format post
        include_sensitive = (
            user_id and 
            (str(post.get('user_id')) == str(user_id) or user_type in ['admin', 'moderator'])
        )
        formatted_post = format_user_post(post, include_sensitive=include_sensitive)
        
        return jsonify({
            'success': True,
            'message': 'Post details retrieved successfully',
            'data': {
                'post': formatted_post
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get post details error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve post details',
            'message': 'An error occurred while retrieving post details'
        }), 500


@bp.route('/posts/<post_id>', methods=['PUT'])
@auth_required()
def update_user_post(post_id):
    """Update a user's post"""
    try:
        # Validate post ID
        if not ObjectId.is_valid(post_id):
            return jsonify({
                'success': False,
                'error': 'Invalid post ID',
                'message': 'The provided post ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Get post
        post = posts_model.find_one({'_id': ObjectId(post_id)})
        
        if not post:
            return jsonify({
                'success': False,
                'error': 'Post not found',
                'message': 'The requested post could not be found'
            }), 404
        
        # Check if user owns the post
        if str(post['user_id']) != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You can only edit your own posts'
            }), 403
        
        # Validate update data
        validation_errors = validate_content_data(data, 'post')
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'message': 'Post validation failed',
                'details': validation_errors
            }), 400
        
        # Build update data
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        # Update content
        if 'content' in data:
            content = data['content'].strip()
            update_data['content'] = content
            update_data['hashtags'] = extract_hashtags(content)
        
        # Update visibility
        if 'visibility' in data and data['visibility'] in ['public', 'private']:
            update_data['visibility'] = data['visibility']
        
        # Update post
        success = posts_model.update_by_id(ObjectId(post_id), update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update post in database'
            }), 500
        
        # Get updated post
        updated_post = posts_model.find_one({'_id': ObjectId(post_id)})
        formatted_post = format_user_post(updated_post)
        
        logger.info(f"Post updated by user {request.current_user['username']}: {post_id}")
        
        return jsonify({
            'success': True,
            'message': 'Post updated successfully',
            'data': {
                'post': formatted_post
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update post error: {e}")
        error_log_model.log_error(
            service_name="user_content_api",
            error_type="update_post_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            context={'post_id': post_id},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to update post',
            'message': 'An error occurred while updating your post'
        }), 500


@bp.route('/posts/<post_id>', methods=['DELETE'])
@auth_required()
def delete_user_post(post_id):
    """Delete a user's post"""
    try:
        # Validate post ID
        if not ObjectId.is_valid(post_id):
            return jsonify({
                'success': False,
                'error': 'Invalid post ID',
                'message': 'The provided post ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        user_type = request.current_user['user_type']
        
        # Get post
        post = posts_model.find_one({'_id': ObjectId(post_id)})
        
        if not post:
            return jsonify({
                'success': False,
                'error': 'Post not found',
                'message': 'The requested post could not be found'
            }), 404
        
        # Check permissions (user can delete their own posts, admins/moderators can delete any)
        can_delete = (
            str(post['user_id']) == str(user_id) or 
            user_type in ['admin', 'moderator']
        )
        
        if not can_delete:
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You can only delete your own posts'
            }), 403
        
        # Delete post
        success = posts_model.delete_by_id(ObjectId(post_id))
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Deletion failed',
                'message': 'Failed to delete post from database'
            }), 500
        
        # Update user statistics if user deleted their own post
        if str(post['user_id']) == str(user_id):
            user = users_model.find_one({'_id': ObjectId(user_id)})
            if user:
                current_count = user.get('statistics', {}).get('posts_created', 0)
                users_model.update_by_id(ObjectId(user_id), {
                    'statistics.posts_created': max(0, current_count - 1)
                })
        
        logger.info(f"Post deleted by user {request.current_user['username']}: {post_id}")
        
        return jsonify({
            'success': True,
            'message': 'Post deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete post error: {e}")
        error_log_model.log_error(
            service_name="user_content_api",
            error_type="delete_post_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            context={'post_id': post_id},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to delete post',
            'message': 'An error occurred while deleting your post'
        }), 500


@bp.route('/posts/<post_id>/like', methods=['POST'])
@auth_required()
def like_post(post_id):
    """Like or unlike a post"""
    try:
        # Validate post ID
        if not ObjectId.is_valid(post_id):
            return jsonify({
                'success': False,
                'error': 'Invalid post ID',
                'message': 'The provided post ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        
        # Get post
        post = posts_model.find_one({'_id': ObjectId(post_id)})
        
        if not post:
            return jsonify({
                'success': False,
                'error': 'Post not found',
                'message': 'The requested post could not be found'
            }), 404
        
        # Check if post is public or user can access it
        if post.get('visibility') != 'public' and str(post.get('user_id')) != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You cannot like this post'
            }), 403
        
        # TODO: In a full implementation, you'd track individual likes in a separate collection
        # For simplicity, we'll just increment/decrement the like count
        data = request.get_json() or {}
        action = data.get('action', 'like')  # 'like' or 'unlike'
        
        if action == 'like':
            # Increment like count
            update_result = posts_model.update_by_id(ObjectId(post_id), {
                '$inc': {'engagement.likes': 1}
            })
            message = 'Post liked successfully'
        elif action == 'unlike':
            # Decrement like count (don't go below 0)
            current_likes = post.get('engagement', {}).get('likes', 0)
            new_likes = max(0, current_likes - 1)
            update_result = posts_model.update_by_id(ObjectId(post_id), {
                'engagement.likes': new_likes
            })
            message = 'Post unliked successfully'
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid action',
                'message': 'Action must be "like" or "unlike"'
            }), 400
        
        if not update_result:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update post engagement'
            }), 500
        
        # Get updated post
        updated_post = posts_model.find_one({'_id': ObjectId(post_id)})
        
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'likes': updated_post.get('engagement', {}).get('likes', 0),
                'action_performed': action
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Like post error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to like post',
            'message': 'An error occurred while liking the post'
        }), 500


# =====================================================
# MEDIA UPLOAD PLACEHOLDER
# =====================================================

@bp.route('/reports/<report_id>/media', methods=['POST'])
@auth_required()
def upload_report_media(report_id):
    """Upload media files to a report (placeholder implementation)"""
    try:
        # TODO: Implement actual file upload functionality
        # This would involve:
        # 1. Validating file types and sizes
        # 2. Storing files securely (cloud storage, local storage)
        # 3. Generating thumbnails for images
        # 4. Virus scanning
        # 5. Updating report with media references
        
        return jsonify({
            'success': False,
            'error': 'Feature not implemented',
            'message': 'Media upload functionality will be implemented when file storage is configured'
        }), 501
        
    except Exception as e:
        logger.error(f"Upload media error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to upload media',
            'message': 'An error occurred while uploading media'
        }), 500


# =====================================================
# CONTENT STATISTICS
# =====================================================

@bp.route('/content/statistics', methods=['GET'])
@auth_required()
def get_content_statistics():
    """Get user's content statistics"""
    try:
        user_id = request.current_user['id']
        
        # Get time range
        days = min(365, int(request.args.get('days', 30)))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get content statistics
        stats = {
            'reports': {
                'total': user_reports_model.count({'user_id': ObjectId(user_id)}),
                'recent': user_reports_model.count({
                    'user_id': ObjectId(user_id),
                    'created_at': {'$gte': start_date}
                }),
                'verified': user_reports_model.count({
                    'user_id': ObjectId(user_id),
                    'verification_status': 'verified'
                }),
                'pending': user_reports_model.count({
                    'user_id': ObjectId(user_id),
                    'verification_status': 'pending'
                })
            },
            'posts': {
                'total': posts_model.count({'user_id': ObjectId(user_id)}),
                'recent': posts_model.count({
                    'user_id': ObjectId(user_id),
                    'created_at': {'$gte': start_date}
                }),
                'public': posts_model.count({
                    'user_id': ObjectId(user_id),
                    'visibility': 'public'
                }),
                'total_likes': 0  # TODO: Calculate from actual posts
            }
        }
        
        # Calculate total likes from user's posts
        try:
            user_posts = list(posts_model.find_many({
                'user_id': ObjectId(user_id)
            }, projection={'engagement.likes': 1}))
            
            total_likes = sum(
                post.get('engagement', {}).get('likes', 0) 
                for post in user_posts
            )
            stats['posts']['total_likes'] = total_likes
        except Exception as e:
            logger.warning(f"Failed to calculate total likes: {e}")
        
        # Calculate verification rate
        total_reports = stats['reports']['total']
        verified_reports = stats['reports']['verified']
        verification_rate = verified_reports / total_reports if total_reports > 0 else 0
        
        stats['summary'] = {
            'verification_rate': verification_rate,
            'content_score': min(100, (verified_reports * 10) + (stats['posts']['total_likes'] * 2)),
            'activity_level': 'high' if stats['reports']['recent'] + stats['posts']['recent'] > 5 else 'medium' if stats['reports']['recent'] + stats['posts']['recent'] > 1 else 'low',
            'time_period_days': days
        }
        
        return jsonify({
            'success': True,
            'message': 'Content statistics retrieved successfully',
            'data': {
                'statistics': stats,
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get content statistics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': 'An error occurred while retrieving content statistics'
        }), 500


# =====================================================
# HEALTH CHECK
# =====================================================

@bp.route('/content/health', methods=['GET'])
def user_content_health_check():
    """User content service health check"""
    try:
        # Test database connectivity
        reports_count = user_reports_model.count()
        posts_count = posts_model.count()
        
        return jsonify({
            'success': True,
            'message': 'User content service is healthy',
            'data': {
                'service': 'user_content_api',
                'status': 'healthy',
                'database_connected': True,
                'total_reports': reports_count,
                'total_posts': posts_count,
                'features': {
                    'protest_reports': True,
                    'user_posts': True,
                    'content_editing': True,
                    'engagement_tracking': True,
                    'media_upload': False,  # Not implemented yet
                    'content_moderation': True,
                    'hashtag_support': True
                },
                'simplified_features': {
                    'auto_approval': True,
                    'basic_validation': True,
                    'simple_engagement': True
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"User content health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'User content service unhealthy',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['bp']