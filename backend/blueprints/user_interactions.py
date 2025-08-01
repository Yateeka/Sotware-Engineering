
"""
User Interactions Blueprint - Social Features & User Engagement
- Bookmarking protests
- Following protests for updates
- User social interactions
- Engagement tracking
- Personal collections and lists
- Activity feeds and notifications
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
import logging

# Initialize blueprint
bp = Blueprint('user_interactions', __name__)
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
    from models.web_app_models import UserBookmarks, UserFollows, Users
    from models.data_collection_models import Protest
    from models.system_monitoring_models import ErrorLog
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # Mock models for development
    class UserBookmarks:
        def __init__(self): pass
        def create(self, data): return ObjectId()
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
        def delete_many(self, query): return True
        def count(self, query=None): return 0
    
    class UserFollows:
        def __init__(self): pass
        def create(self, data): return ObjectId()
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
        def update_by_id(self, id, data): return True
        def delete_many(self, query): return True
        def count(self, query=None): return 0
    
    class Users:
        def __init__(self): pass
        def find_one(self, query): return None
        def update_by_id(self, id, data): return True
    
    class Protest:
        def __init__(self): pass
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
        def update_by_id(self, id, data): return True
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass

# Initialize models
bookmarks_model = UserBookmarks()
follows_model = UserFollows()
users_model = Users()
protest_model = Protest()
error_log_model = ErrorLog()


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def format_bookmark(bookmark, include_protest_details=True):
    """Format bookmark data for API response"""
    try:
        if not bookmark:
            return None
        
        formatted = {
            'bookmark_id': str(bookmark['_id']),
            'protest_id': str(bookmark['protest_id']),
            'created_at': bookmark.get('created_at').isoformat() if bookmark.get('created_at') else None,
            'notes': bookmark.get('notes', ''),
            'tags': bookmark.get('tags', []),
            'is_favorite': bookmark.get('is_favorite', False)
        }
        
        # Include protest details if requested and available
        if include_protest_details and 'protest_details' in bookmark:
            protest = bookmark['protest_details']
            formatted['protest'] = {
                'title': protest.get('title', ''),
                'location_description': protest.get('location_description', ''),
                'categories': protest.get('categories', []),
                'status': protest.get('status', 'active'),
                'start_date': protest.get('start_date').isoformat() if protest.get('start_date') else None,
                'verification_status': protest.get('verification_status', 'unverified')
            }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting bookmark: {e}")
        return None

def format_follow(follow, include_protest_details=True):
    """Format follow data for API response"""
    try:
        if not follow:
            return None
        
        formatted = {
            'follow_id': str(follow['_id']),
            'protest_id': str(follow['protest_id']),
            'created_at': follow.get('created_at').isoformat() if follow.get('created_at') else None,
            'active': follow.get('active', True),
            'notification_enabled': follow.get('notification_enabled', True),
            'last_update_seen': follow.get('last_update_seen').isoformat() if follow.get('last_update_seen') else None,
            'follow_reason': follow.get('follow_reason', '')
        }
        
        # Include protest details if requested and available
        if include_protest_details and 'protest_details' in follow:
            protest = follow['protest_details']
            formatted['protest'] = {
                'title': protest.get('title', ''),
                'location_description': protest.get('location_description', ''),
                'categories': protest.get('categories', []),
                'status': protest.get('status', 'active'),
                'start_date': protest.get('start_date').isoformat() if protest.get('start_date') else None,
                'verification_status': protest.get('verification_status', 'unverified'),
                'last_updated': protest.get('updated_at').isoformat() if protest.get('updated_at') else None
            }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting follow: {e}")
        return None

def validate_protest_exists(protest_id):
    """Validate that a protest exists and is accessible"""
    try:
        if not ObjectId.is_valid(protest_id):
            return False, 'Invalid protest ID format'
        
        protest = protest_model.find_one({
            '_id': ObjectId(protest_id),
            'visibility': 'public'
        })
        
        if not protest:
            return False, 'Protest not found or not accessible'
        
        return True, protest
        
    except Exception as e:
        logger.error(f"Error validating protest: {e}")
        return False, 'Error validating protest'


# =====================================================
# BOOKMARK ENDPOINTS
# =====================================================

@bp.route('/bookmarks', methods=['POST'])
@auth_required()
def bookmark_protest():
    """Bookmark a protest"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data or not data.get('protest_id'):
            return jsonify({
                'success': False,
                'error': 'Missing protest ID',
                'message': 'Protest ID is required'
            }), 400
        
        protest_id = data['protest_id']
        
        # Validate protest exists
        is_valid, protest_or_error = validate_protest_exists(protest_id)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Invalid protest',
                'message': protest_or_error
            }), 404
        
        # Check if already bookmarked
        existing_bookmark = bookmarks_model.find_one({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id)
        })
        
        if existing_bookmark:
            return jsonify({
                'success': False,
                'error': 'Already bookmarked',
                'message': 'This protest is already in your bookmarks'
            }), 409
        
        # Create bookmark
        bookmark_data = {
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id),
            'created_at': datetime.utcnow(),
            'notes': data.get('notes', '').strip(),
            'tags': [tag.strip().lower() for tag in data.get('tags', [])],
            'is_favorite': data.get('is_favorite', False),
            'metadata': {
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'bookmark_source': 'web_interface'
            }
        }
        
        bookmark_id = bookmarks_model.create(bookmark_data)
        
        try:
            protest_model.update_by_id(ObjectId(protest_id), {
                '$inc': {'engagement_metrics.bookmarks': 1}
            })
        except Exception as e:
            logger.warning(f"Failed to update protest engagement metrics: {e}")
        
        # Get created bookmark with protest details
        created_bookmark = bookmarks_model.find_one({'_id': bookmark_id})
        formatted_bookmark = format_bookmark(created_bookmark, include_protest_details=False)
        
        logger.info(f"Protest bookmarked by user {request.current_user['username']}: {protest_id}")
        
        return jsonify({
            'success': True,
            'message': 'Protest bookmarked successfully',
            'data': {
                'bookmark': formatted_bookmark,
                'protest_title': protest_or_error.get('title', '')
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Bookmark protest error: {e}")
        error_log_model.log_error(
            service_name="user_interactions_api",
            error_type="bookmark_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to bookmark protest',
            'message': 'An error occurred while bookmarking the protest'
        }), 500


@bp.route('/bookmarks', methods=['GET'])
@auth_required()
def get_user_bookmarks():
    """Get user's bookmarked protests"""
    try:
        user_id = request.current_user['id']
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Parse filters
        filters = {'user_id': ObjectId(user_id)}
        
        # Filter by tags
        tags = request.args.getlist('tags')
        if tags:
            filters['tags'] = {'$in': [tag.lower() for tag in tags]}
        
        # Filter by favorites
        if request.args.get('favorites_only') == 'true':
            filters['is_favorite'] = True
        
        # Get bookmarks with protest details using aggregation
        pipeline = [
            {'$match': filters},
            {
                '$lookup': {
                    'from': 'protests',
                    'localField': 'protest_id',
                    'foreignField': '_id',
                    'as': 'protest_details'
                }
            },
            {'$unwind': '$protest_details'},
            {'$sort': {'created_at': -1}},
            {'$skip': offset},
            {'$limit': limit}
        ]
        
        try:
            bookmarks = list(bookmarks_model.collection.aggregate(pipeline))
        except Exception:
            # Fallback: get bookmarks without protest details
            bookmarks = list(bookmarks_model.find_many(
                filters,
                sort=[('created_at', -1)],
                limit=limit,
                skip=offset
            ))
        
        # Get total count
        total_count = bookmarks_model.count(filters)
        
        # Format bookmarks
        formatted_bookmarks = []
        for bookmark in bookmarks:
            formatted_bookmark = format_bookmark(bookmark, include_protest_details=True)
            if formatted_bookmark:
                formatted_bookmarks.append(formatted_bookmark)
        
        # Pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_bookmarks)} bookmarks',
            'data': {
                'bookmarks': formatted_bookmarks,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'filters_applied': {
                    'tags': tags,
                    'favorites_only': request.args.get('favorites_only') == 'true'
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user bookmarks error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve bookmarks',
            'message': 'An error occurred while retrieving your bookmarks'
        }), 500


@bp.route('/bookmarks/<protest_id>', methods=['DELETE'])
@auth_required()
def remove_bookmark(protest_id):
    """Remove a protest from bookmarks"""
    try:
        # Validate protest ID
        if not ObjectId.is_valid(protest_id):
            return jsonify({
                'success': False,
                'error': 'Invalid protest ID',
                'message': 'The provided protest ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        
        # Check if bookmark exists
        existing_bookmark = bookmarks_model.find_one({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id)
        })
        
        if not existing_bookmark:
            return jsonify({
                'success': False,
                'error': 'Bookmark not found',
                'message': 'This protest is not in your bookmarks'
            }), 404
        
        # Remove bookmark
        success = bookmarks_model.delete_many({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id)
        })
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Removal failed',
                'message': 'Failed to remove bookmark'
            }), 500
        
        # Update protest engagement metrics
        try:
            protest_model.update_by_id(ObjectId(protest_id), {
                '$inc': {'engagement_metrics.bookmarks': -1}
            })
        except Exception as e:
            logger.warning(f"Failed to update protest engagement metrics: {e}")
        
        logger.info(f"Bookmark removed by user {request.current_user['username']}: {protest_id}")
        
        return jsonify({
            'success': True,
            'message': 'Bookmark removed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Remove bookmark error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to remove bookmark',
            'message': 'An error occurred while removing the bookmark'
        }), 500


@bp.route('/bookmarks/<protest_id>', methods=['PUT'])
@auth_required()
def update_bookmark(protest_id):
    """Update bookmark notes, tags, or favorite status"""
    try:
        # Validate protest ID
        if not ObjectId.is_valid(protest_id):
            return jsonify({
                'success': False,
                'error': 'Invalid protest ID',
                'message': 'The provided protest ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Check if bookmark exists
        existing_bookmark = bookmarks_model.find_one({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id)
        })
        
        if not existing_bookmark:
            return jsonify({
                'success': False,
                'error': 'Bookmark not found',
                'message': 'This protest is not in your bookmarks'
            }), 404
        
        # Build update data
        update_data = {}
        
        # Update notes
        if 'notes' in data:
            update_data['notes'] = data['notes'].strip()
        
        # Update tags
        if 'tags' in data:
            update_data['tags'] = [tag.strip().lower() for tag in data['tags']]
        
        # Update favorite status
        if 'is_favorite' in data and isinstance(data['is_favorite'], bool):
            update_data['is_favorite'] = data['is_favorite']
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No updates provided',
                'message': 'No valid update fields were provided'
            }), 400
        
        # Update bookmark
        success = bookmarks_model.update_by_id(existing_bookmark['_id'], update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update bookmark'
            }), 500
        
        # Get updated bookmark
        updated_bookmark = bookmarks_model.find_one({'_id': existing_bookmark['_id']})
        formatted_bookmark = format_bookmark(updated_bookmark)
        
        return jsonify({
            'success': True,
            'message': 'Bookmark updated successfully',
            'data': {
                'bookmark': formatted_bookmark
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update bookmark error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update bookmark',
            'message': 'An error occurred while updating the bookmark'
        }), 500


# =====================================================
# FOLLOW ENDPOINTS
# =====================================================

@bp.route('/follows', methods=['POST'])
@auth_required()
def follow_protest():
    """Follow a protest for updates"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data or not data.get('protest_id'):
            return jsonify({
                'success': False,
                'error': 'Missing protest ID',
                'message': 'Protest ID is required'
            }), 400
        
        protest_id = data['protest_id']
        
        # Validate protest exists
        is_valid, protest_or_error = validate_protest_exists(protest_id)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Invalid protest',
                'message': protest_or_error
            }), 404
        
        # Check if already following
        existing_follow = follows_model.find_one({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id),
            'active': True
        })
        
        if existing_follow:
            return jsonify({
                'success': False,
                'error': 'Already following',
                'message': 'You are already following this protest'
            }), 409
        
        # Create follow
        follow_data = {
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id),
            'created_at': datetime.utcnow(),
            'active': True,
            'notification_enabled': data.get('notification_enabled', True),
            'follow_reason': data.get('follow_reason', '').strip(),
            'last_update_seen': datetime.utcnow(),
            'metadata': {
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'follow_source': 'web_interface'
            }
        }
        
        follow_id = follows_model.create(follow_data)
        
        # Update protest engagement metrics
        try:
            protest_model.update_by_id(ObjectId(protest_id), {
                '$inc': {'engagement_metrics.followers': 1}
            })
        except Exception as e:
            logger.warning(f"Failed to update protest engagement metrics: {e}")
        
        # Get created follow
        created_follow = follows_model.find_one({'_id': follow_id})
        formatted_follow = format_follow(created_follow, include_protest_details=False)
        
        logger.info(f"Protest followed by user {request.current_user['username']}: {protest_id}")
        
        return jsonify({
            'success': True,
            'message': 'Protest followed successfully',
            'data': {
                'follow': formatted_follow,
                'protest_title': protest_or_error.get('title', '')
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Follow protest error: {e}")
        error_log_model.log_error(
            service_name="user_interactions_api",
            error_type="follow_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to follow protest',
            'message': 'An error occurred while following the protest'
        }), 500


@bp.route('/follows', methods=['GET'])
@auth_required()
def get_user_follows():
    """Get user's followed protests"""
    try:
        user_id = request.current_user['id']
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Parse filters
        filters = {
            'user_id': ObjectId(user_id),
            'active': True
        }
        
        # Filter by notification status
        if request.args.get('notifications_enabled') == 'true':
            filters['notification_enabled'] = True
        elif request.args.get('notifications_enabled') == 'false':
            filters['notification_enabled'] = False
        
        # Get follows with protest details using aggregation
        pipeline = [
            {'$match': filters},
            {
                '$lookup': {
                    'from': 'protests',
                    'localField': 'protest_id',
                    'foreignField': '_id',
                    'as': 'protest_details'
                }
            },
            {'$unwind': '$protest_details'},
            {'$sort': {'created_at': -1}},
            {'$skip': offset},
            {'$limit': limit}
        ]
        
        try:
            follows = list(follows_model.collection.aggregate(pipeline))
        except Exception:
            # Fallback: get follows without protest details
            follows = list(follows_model.find_many(
                filters,
                sort=[('created_at', -1)],
                limit=limit,
                skip=offset
            ))
        
        # Get total count
        total_count = follows_model.count(filters)
        
        # Format follows
        formatted_follows = []
        for follow in follows:
            formatted_follow = format_follow(follow, include_protest_details=True)
            if formatted_follow:
                formatted_follows.append(formatted_follow)
        
        # Pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_follows)} follows',
            'data': {
                'follows': formatted_follows,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'filters_applied': {
                    'notifications_enabled': request.args.get('notifications_enabled')
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user follows error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve follows',
            'message': 'An error occurred while retrieving your follows'
        }), 500


@bp.route('/follows/<protest_id>', methods=['DELETE'])
@auth_required()
def unfollow_protest(protest_id):
    """Unfollow a protest"""
    try:
        # Validate protest ID
        if not ObjectId.is_valid(protest_id):
            return jsonify({
                'success': False,
                'error': 'Invalid protest ID',
                'message': 'The provided protest ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        
        # Check if follow exists
        existing_follow = follows_model.find_one({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id),
            'active': True
        })
        
        if not existing_follow:
            return jsonify({
                'success': False,
                'error': 'Follow not found',
                'message': 'You are not following this protest'
            }), 404
        
        # Mark follow as inactive instead of deleting
        success = follows_model.update_by_id(existing_follow['_id'], {
            'active': False,
            'unfollowed_at': datetime.utcnow()
        })
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Unfollow failed',
                'message': 'Failed to unfollow protest'
            }), 500
        
        # Update protest engagement metrics
        try:
            protest_model.update_by_id(ObjectId(protest_id), {
                '$inc': {'engagement_metrics.followers': -1}
            })
        except Exception as e:
            logger.warning(f"Failed to update protest engagement metrics: {e}")
        
        logger.info(f"Protest unfollowed by user {request.current_user['username']}: {protest_id}")
        
        return jsonify({
            'success': True,
            'message': 'Protest unfollowed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Unfollow protest error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to unfollow protest',
            'message': 'An error occurred while unfollowing the protest'
        }), 500


@bp.route('/follows/<protest_id>', methods=['PUT'])
@auth_required()
def update_follow_settings(protest_id):
    """Update follow settings (notifications, etc.)"""
    try:
        # Validate protest ID
        if not ObjectId.is_valid(protest_id):
            return jsonify({
                'success': False,
                'error': 'Invalid protest ID',
                'message': 'The provided protest ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        # Check if follow exists
        existing_follow = follows_model.find_one({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id),
            'active': True
        })
        
        if not existing_follow:
            return jsonify({
                'success': False,
                'error': 'Follow not found',
                'message': 'You are not following this protest'
            }), 404
        
        # Build update data
        update_data = {}
        
        # Update notification settings
        if 'notification_enabled' in data and isinstance(data['notification_enabled'], bool):
            update_data['notification_enabled'] = data['notification_enabled']
        
        # Update follow reason
        if 'follow_reason' in data:
            update_data['follow_reason'] = data['follow_reason'].strip()
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No updates provided',
                'message': 'No valid update fields were provided'
            }), 400
        
        # Update follow
        success = follows_model.update_by_id(existing_follow['_id'], update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Update failed',
                'message': 'Failed to update follow settings'
            }), 500
        
        # Get updated follow
        updated_follow = follows_model.find_one({'_id': existing_follow['_id']})
        formatted_follow = format_follow(updated_follow)
        
        return jsonify({
            'success': True,
            'message': 'Follow settings updated successfully',
            'data': {
                'follow': formatted_follow
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update follow settings error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update follow settings',
            'message': 'An error occurred while updating follow settings'
        }), 500


# =====================================================
# INTERACTION STATUS ENDPOINTS
# =====================================================

@bp.route('/interactions/status/<protest_id>', methods=['GET'])
@auth_required()
def get_interaction_status(protest_id):
    """Get user's interaction status with a specific protest"""
    try:
        # Validate protest ID
        if not ObjectId.is_valid(protest_id):
            return jsonify({
                'success': False,
                'error': 'Invalid protest ID',
                'message': 'The provided protest ID is not valid'
            }), 400
        
        user_id = request.current_user['id']
        
        # Check bookmark status
        bookmark = bookmarks_model.find_one({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id)
        })
        
        # Check follow status
        follow = follows_model.find_one({
            'user_id': ObjectId(user_id),
            'protest_id': ObjectId(protest_id),
            'active': True
        })
        
        # Get protest details for context
        protest = protest_model.find_one({'_id': ObjectId(protest_id)})
        
        interaction_status = {
            'protest_id': protest_id,
            'is_bookmarked': bookmark is not None,
            'is_following': follow is not None,
            'bookmark_details': format_bookmark(bookmark) if bookmark else None,
            'follow_details': format_follow(follow) if follow else None,
            'protest_engagement': {
                'bookmarks': protest.get('engagement_metrics', {}).get('bookmarks', 0) if protest else 0,
                'followers': protest.get('engagement_metrics', {}).get('followers', 0) if protest else 0,
                'views': protest.get('engagement_metrics', {}).get('views', 0) if protest else 0
            } if protest else {}
        }
        
        return jsonify({
            'success': True,
            'message': 'Interaction status retrieved successfully',
            'data': interaction_status
        }), 200
        
    except Exception as e:
        logger.error(f"Get interaction status error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve interaction status',
            'message': 'An error occurred while retrieving interaction status'
        }), 500


@bp.route('/interactions/bulk-status', methods=['POST'])
@auth_required()
def get_bulk_interaction_status():
    """Get user's interaction status for multiple protests"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data or not data.get('protest_ids'):
            return jsonify({
                'success': False,
                'error': 'Missing protest IDs',
                'message': 'A list of protest IDs is required'
            }), 400
        
        protest_ids = data['protest_ids']
        
        # Validate protest IDs
        valid_ids = []
        for protest_id in protest_ids:
            if ObjectId.is_valid(protest_id):
                valid_ids.append(ObjectId(protest_id))
        
        if not valid_ids:
            return jsonify({
                'success': False,
                'error': 'No valid protest IDs',
                'message': 'No valid protest IDs were provided'
            }), 400
        
        # Get bookmarks for these protests
        bookmarks = list(bookmarks_model.find_many({
            'user_id': ObjectId(user_id),
            'protest_id': {'$in': valid_ids}
        }))
        
        # Get follows for these protests
        follows = list(follows_model.find_many({
            'user_id': ObjectId(user_id),
            'protest_id': {'$in': valid_ids},
            'active': True
        }))
        
        # Create lookup dictionaries
        bookmark_lookup = {str(b['protest_id']): b for b in bookmarks}
        follow_lookup = {str(f['protest_id']): f for f in follows}
        
        # Build response
        interaction_statuses = {}
        for protest_id in protest_ids:
            if ObjectId.is_valid(protest_id):
                interaction_statuses[protest_id] = {
                    'is_bookmarked': protest_id in bookmark_lookup,
                    'is_following': protest_id in follow_lookup,
                    'bookmark_created_at': bookmark_lookup[protest_id].get('created_at').isoformat() if protest_id in bookmark_lookup else None,
                    'follow_created_at': follow_lookup[protest_id].get('created_at').isoformat() if protest_id in follow_lookup else None
                }
        
        return jsonify({
            'success': True,
            'message': f'Retrieved interaction status for {len(interaction_statuses)} protests',
            'data': {
                'interaction_statuses': interaction_statuses,
                'summary': {
                    'total_requested': len(protest_ids),
                    'total_bookmarked': len(bookmarks),
                    'total_following': len(follows)
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get bulk interaction status error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve bulk interaction status',
            'message': 'An error occurred while retrieving interaction status'
        }), 500


# =====================================================
# USER ACTIVITY FEED
# =====================================================

@bp.route('/interactions/activity', methods=['GET'])
@auth_required()
def get_user_activity_feed():
    """Get user's recent interaction activity"""
    try:
        user_id = request.current_user['id']
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Get time range
        days = min(90, int(request.args.get('days', 30)))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recent bookmarks
        recent_bookmarks = list(bookmarks_model.find_many({
            'user_id': ObjectId(user_id),
            'created_at': {'$gte': start_date}
        }, sort=[('created_at', -1)], limit=limit))
        
        # Get recent follows
        recent_follows = list(follows_model.find_many({
            'user_id': ObjectId(user_id),
            'created_at': {'$gte': start_date}
        }, sort=[('created_at', -1)], limit=limit))
        
        # Combine and sort activities
        activities = []
        
        for bookmark in recent_bookmarks:
            activities.append({
                'type': 'bookmark',
                'action': 'bookmarked',
                'protest_id': str(bookmark['protest_id']),
                'timestamp': bookmark['created_at'],
                'details': {
                    'is_favorite': bookmark.get('is_favorite', False),
                    'tags': bookmark.get('tags', [])
                }
            })
        
        for follow in recent_follows:
            if follow.get('active', True):
                activities.append({
                    'type': 'follow',
                    'action': 'followed',
                    'protest_id': str(follow['protest_id']),
                    'timestamp': follow['created_at'],
                    'details': {
                        'notification_enabled': follow.get('notification_enabled', True),
                        'follow_reason': follow.get('follow_reason', '')
                    }
                })
            else:
                activities.append({
                    'type': 'follow',
                    'action': 'unfollowed',
                    'protest_id': str(follow['protest_id']),
                    'timestamp': follow.get('unfollowed_at', follow['created_at']),
                    'details': {}
                })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply pagination
        paginated_activities = activities[offset:offset + limit]
        
        # Format timestamps
        for activity in paginated_activities:
            activity['timestamp'] = activity['timestamp'].isoformat()
        
        # Calculate pagination info
        total_count = len(activities)
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(paginated_activities)} activities',
            'data': {
                'activities': paginated_activities,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'summary': {
                    'time_period_days': days,
                    'total_bookmarks': len(recent_bookmarks),
                    'total_follows': len([f for f in recent_follows if f.get('active', True)]),
                    'total_unfollows': len([f for f in recent_follows if not f.get('active', True)])
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user activity feed error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve activity feed',
            'message': 'An error occurred while retrieving your activity feed'
        }), 500


# =====================================================
# INTERACTION STATISTICS
# =====================================================

@bp.route('/interactions/statistics', methods=['GET'])
@auth_required()
def get_interaction_statistics():
    """Get user's interaction statistics"""
    try:
        user_id = request.current_user['id']
        
        # Get time range
        days = min(365, int(request.args.get('days', 90)))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Calculate statistics
        stats = {
            'bookmarks': {
                'total': bookmarks_model.count({'user_id': ObjectId(user_id)}),
                'recent': bookmarks_model.count({
                    'user_id': ObjectId(user_id),
                    'created_at': {'$gte': start_date}
                }),
                'favorites': bookmarks_model.count({
                    'user_id': ObjectId(user_id),
                    'is_favorite': True
                })
            },
            'follows': {
                'total': follows_model.count({
                    'user_id': ObjectId(user_id),
                    'active': True
                }),
                'recent': follows_model.count({
                    'user_id': ObjectId(user_id),
                    'created_at': {'$gte': start_date}
                }),
                'with_notifications': follows_model.count({
                    'user_id': ObjectId(user_id),
                    'active': True,
                    'notification_enabled': True
                })
            }
        }
        
        # Get most used bookmark tags
        try:
            bookmark_tags_pipeline = [
                {'$match': {'user_id': ObjectId(user_id)}},
                {'$unwind': '$tags'},
                {'$group': {'_id': '$tags', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            
            tag_results = list(bookmarks_model.collection.aggregate(bookmark_tags_pipeline))
            most_used_tags = [
                {'tag': result['_id'], 'count': result['count']}
                for result in tag_results
            ]
        except Exception:
            most_used_tags = []
        
        # Calculate engagement score
        engagement_score = (
            stats['bookmarks']['total'] * 2 +
            stats['follows']['total'] * 3 +
            stats['bookmarks']['favorites'] * 5
        )
        
        activity_level = 'high' if engagement_score > 50 else 'medium' if engagement_score > 10 else 'low'
        
        return jsonify({
            'success': True,
            'message': 'Interaction statistics retrieved successfully',
            'data': {
                'statistics': stats,
                'engagement': {
                    'score': engagement_score,
                    'level': activity_level,
                    'most_used_bookmark_tags': most_used_tags
                },
                'summary': {
                    'total_interactions': stats['bookmarks']['total'] + stats['follows']['total'],
                    'recent_interactions': stats['bookmarks']['recent'] + stats['follows']['recent'],
                    'time_period_days': days
                },
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get interaction statistics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': 'An error occurred while retrieving interaction statistics'
        }), 500


# =====================================================
# BULK OPERATIONS
# =====================================================

@bp.route('/bookmarks/bulk-remove', methods=['POST'])
@auth_required()
def bulk_remove_bookmarks():
    """Remove multiple bookmarks at once"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data or not data.get('protest_ids'):
            return jsonify({
                'success': False,
                'error': 'Missing protest IDs',
                'message': 'A list of protest IDs is required'
            }), 400
        
        protest_ids = data['protest_ids']
        
        # Validate protest IDs
        valid_ids = []
        for protest_id in protest_ids:
            if ObjectId.is_valid(protest_id):
                valid_ids.append(ObjectId(protest_id))
        
        if not valid_ids:
            return jsonify({
                'success': False,
                'error': 'No valid protest IDs',
                'message': 'No valid protest IDs were provided'
            }), 400
        
        # Remove bookmarks
        result = bookmarks_model.delete_many({
            'user_id': ObjectId(user_id),
            'protest_id': {'$in': valid_ids}
        })
        
        # Update protest engagement metrics for each removed bookmark
        for protest_id in valid_ids:
            try:
                protest_model.update_by_id(protest_id, {
                    '$inc': {'engagement_metrics.bookmarks': -1}
                })
            except Exception as e:
                logger.warning(f"Failed to update engagement metrics for {protest_id}: {e}")
        
        logger.info(f"Bulk bookmark removal by user {request.current_user['username']}: {len(valid_ids)} bookmarks")
        
        return jsonify({
            'success': True,
            'message': f'Successfully removed {len(valid_ids)} bookmarks',
            'data': {
                'removed_count': len(valid_ids),
                'protest_ids': [str(pid) for pid in valid_ids]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Bulk remove bookmarks error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to remove bookmarks',
            'message': 'An error occurred while removing bookmarks'
        }), 500


@bp.route('/follows/bulk-update', methods=['PUT'])
@auth_required()
def bulk_update_follow_notifications():
    """Update notification settings for multiple follows"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        notification_enabled = data.get('notification_enabled')
        protest_ids = data.get('protest_ids', [])
        
        if notification_enabled is None:
            return jsonify({
                'success': False,
                'error': 'Missing notification setting',
                'message': 'notification_enabled field is required'
            }), 400
        
        # If no specific protest IDs provided, update all follows
        filters = {
            'user_id': ObjectId(user_id),
            'active': True
        }
        
        if protest_ids:
            valid_ids = [ObjectId(pid) for pid in protest_ids if ObjectId.is_valid(pid)]
            if valid_ids:
                filters['protest_id'] = {'$in': valid_ids}
        
        # Update follows
        update_result = follows_model.update_many(
            filters,
            {'notification_enabled': notification_enabled}
        )
        
        action = 'enabled' if notification_enabled else 'disabled'
        
        logger.info(f"Bulk notification update by user {request.current_user['username']}: {action} for {update_result.modified_count} follows")
        
        return jsonify({
            'success': True,
            'message': f'Notifications {action} for {update_result.modified_count} follows',
            'data': {
                'updated_count': update_result.modified_count,
                'notification_enabled': notification_enabled
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Bulk update follow notifications error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update notifications',
            'message': 'An error occurred while updating notification settings'
        }), 500


# =====================================================
# DISCOVERY & RECOMMENDATIONS
# =====================================================

@bp.route('/interactions/recommendations', methods=['GET'])
@auth_required()
def get_protest_recommendations():
    """Get protest recommendations based on user's interactions"""
    try:
        user_id = request.current_user['id']
        limit = min(20, int(request.args.get('limit', 10)))
        
        # Get user's bookmarked and followed protest categories
        user_bookmarks = list(bookmarks_model.find_many({
            'user_id': ObjectId(user_id)
        }, projection={'protest_id': 1}))
        
        user_follows = list(follows_model.find_many({
            'user_id': ObjectId(user_id),
            'active': True
        }, projection={'protest_id': 1}))
        
        # Get categories from user's bookmarked/followed protests
        user_protest_ids = []
        user_protest_ids.extend([b['protest_id'] for b in user_bookmarks])
        user_protest_ids.extend([f['protest_id'] for f in user_follows])
        
        user_categories = set()
        if user_protest_ids:
            user_protests = list(protest_model.find_many({
                '_id': {'$in': user_protest_ids}
            }, projection={'categories': 1}))
            
            for protest in user_protests:
                user_categories.update(protest.get('categories', []))
        
        # If user has no interactions, use popular categories
        if not user_categories:
            user_categories = {'Human Rights', 'Environmental', 'Social Justice'}
        
        # Find recommended protests
        excluded_ids = set(user_protest_ids)
        
        recommended_protests = list(protest_model.find_many({
            '_id': {'$nin': list(excluded_ids)},
            'categories': {'$in': list(user_categories)},
            'visibility': 'public',
            'status': {'$in': ['active', 'ongoing']},
            'verification_status': {'$in': ['verified', 'auto_verified']}
        }, sort=[('trending_score', -1), ('data_quality_score', -1)], limit=limit))
        
        # Format recommendations
        recommendations = []
        for protest in recommended_protests:
            # Calculate match score based on category overlap
            protest_categories = set(protest.get('categories', []))
            match_score = len(protest_categories.intersection(user_categories)) / len(protest_categories) if protest_categories else 0
            
            recommendations.append({
                'protest_id': str(protest['_id']),
                'title': protest.get('title', ''),
                'location_description': protest.get('location_description', ''),
                'categories': protest.get('categories', []),
                'verification_status': protest.get('verification_status', 'unverified'),
                'trending_score': protest.get('trending_score', 0),
                'match_score': round(match_score, 2),
                'recommendation_reason': f'Matches your interest in {", ".join(protest_categories.intersection(user_categories))}'
            })
        
        # Sort by match score and trending score
        recommendations.sort(key=lambda x: (x['match_score'], x['trending_score']), reverse=True)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(recommendations)} recommendations',
            'data': {
                'recommendations': recommendations,
                'based_on': {
                    'user_categories': list(user_categories),
                    'total_bookmarks': len(user_bookmarks),
                    'total_follows': len(user_follows)
                },
                'algorithm': 'category_matching',
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get recommendations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate recommendations',
            'message': 'An error occurred while generating recommendations'
        }), 500


# =====================================================
# HEALTH CHECK
# =====================================================

@bp.route('/interactions/health', methods=['GET'])
def user_interactions_health_check():
    """User interactions service health check"""
    try:
        # Test database connectivity
        bookmarks_count = bookmarks_model.count()
        follows_count = follows_model.count()
        
        return jsonify({
            'success': True,
            'message': 'User interactions service is healthy',
            'data': {
                'service': 'user_interactions_api',
                'status': 'healthy',
                'database_connected': True,
                'total_bookmarks': bookmarks_count,
                'total_follows': follows_count,
                'features': {
                    'bookmarks': True,
                    'follows': True,
                    'bulk_operations': True,
                    'interaction_status': True,
                    'activity_feed': True,
                    'statistics': True,
                    'recommendations': True,
                    'engagement_tracking': True
                },
                'simplified_features': {
                    'basic_engagement_metrics': True,
                    'simple_recommendations': True,
                    'tag_based_organization': True
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"User interactions health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'User interactions service unhealthy',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['bp']# blueprints/user_interactions.py