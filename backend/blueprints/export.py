# blueprints/export.py
"""
Export Blueprint - Data Export & Downloads
- CSV and JSON export for protests and user data
- Async export processing for large datasets
- Export request management and status tracking
- Download links with expiration
- Export history and limits
- User-specific export permissions
"""

import os
import csv
import json
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, send_file
from bson import ObjectId
import logging
import threading
from io import StringIO, BytesIO
import zipfile

# Initialize blueprint
bp = Blueprint('export', __name__)
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
    from models.data_collection_models import Protest
    from models.web_app_models import UserReports, Posts, Users, UserBookmarks, UserFollows
    from models.system_monitoring_models import ErrorLog
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # Mock models for development
    class Protest:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
    
    class UserReports:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
    
    class Posts:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
    
    class Users:
        def __init__(self): pass
        def find_one(self, query): return None
        def update_by_id(self, id, data): return True
    
    class UserBookmarks:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
    
    class UserFollows:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass

# Initialize models
protest_model = Protest()
user_reports_model = UserReports()
posts_model = Posts()
users_model = Users()
bookmarks_model = UserBookmarks()
follows_model = UserFollows()
error_log_model = ErrorLog()


# =====================================================
# EXPORT REQUEST TRACKING (Simplified - In Memory)
# =====================================================

# In production, you'd use a database table for this
export_requests = {}

class ExportRequest:
    def __init__(self, request_id, user_id, export_type, filters, format_type):
        self.request_id = request_id
        self.user_id = user_id
        self.export_type = export_type
        self.filters = filters
        self.format_type = format_type
        self.status = 'queued'
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.file_path = None
        self.file_size = 0
        self.record_count = 0
        self.error_message = None
        self.download_count = 0
        self.expires_at = datetime.utcnow() + timedelta(days=7)


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def get_export_limits(user_type: str) -> dict:
    """Get export limits based on user type"""
    limits = {
        'citizen': {
            'max_records': 1000,
            'max_exports_per_day': 3,
            'formats': ['csv', 'json']
        },
        'activist': {
            'max_records': 5000,
            'max_exports_per_day': 10,
            'formats': ['csv', 'json']
        },
        'journalist': {
            'max_records': 50000,
            'max_exports_per_day': 50,
            'formats': ['csv', 'json']
        },
        'researcher': {
            'max_records': 100000,
            'max_exports_per_day': 100,
            'formats': ['csv', 'json']
        },
        'ngo_worker': {
            'max_records': 30000,
            'max_exports_per_day': 30,
            'formats': ['csv', 'json']
        },
        'moderator': {
            'max_records': 200000,
            'max_exports_per_day': 200,
            'formats': ['csv', 'json']
        },
        'admin': {
            'max_records': -1,  # Unlimited
            'max_exports_per_day': -1,  # Unlimited
            'formats': ['csv', 'json']
        }
    }
    
    return limits.get(user_type, limits['citizen'])

def check_export_limits(user_id: str, user_type: str) -> tuple:
    """Check if user can perform export"""
    limits = get_export_limits(user_type)
    
    # Count exports today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_requests = [
        req for req in export_requests.values()
        if req.user_id == user_id and req.created_at >= today
    ]
    
    daily_limit = limits['max_exports_per_day']
    if daily_limit != -1 and len(today_requests) >= daily_limit:
        return False, f"Daily export limit of {daily_limit} exceeded"
    
    return True, None

def validate_export_filters(filters: dict, export_type: str) -> tuple:
    """Validate export filters"""
    errors = []
    
    # Date range validation
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    
    if start_date and end_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', ''))
            end = datetime.fromisoformat(end_date.replace('Z', ''))
            
            if start > end:
                errors.append("Start date must be before end date")
            
            # Limit date range to prevent huge exports
            if (end - start).days > 365:
                errors.append("Date range cannot exceed 365 days")
                
        except ValueError:
            errors.append("Invalid date format")
    
    # Category validation
    categories = filters.get('categories', [])
    if categories and not isinstance(categories, list):
        errors.append("Categories must be a list")
    
    # Country validation
    countries = filters.get('countries', [])
    if countries and not isinstance(countries, list):
        errors.append("Countries must be a list")
    
    return len(errors) == 0, errors

def build_export_query(filters: dict, export_type: str) -> dict:
    """Build MongoDB query from export filters"""
    query = {}
    
    # Base visibility filter for protests
    if export_type == 'protests':
        query['visibility'] = 'public'
    
    # Date range filter
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter['$gte'] = datetime.fromisoformat(start_date.replace('Z', ''))
        if end_date:
            date_filter['$lte'] = datetime.fromisoformat(end_date.replace('Z', ''))
        
        # Use appropriate date field based on export type
        if export_type == 'protests':
            query['start_date'] = date_filter
        else:
            query['created_at'] = date_filter
    
    # Category filter
    categories = filters.get('categories', [])
    if categories:
        query['categories'] = {'$in': categories}
    
    # Country filter (for protests)
    countries = filters.get('countries', [])
    if countries and export_type == 'protests':
        country_patterns = [{'location_description': {'$regex': country, '$options': 'i'}} for country in countries]
        query['$or'] = country_patterns
    
    # Status filter
    statuses = filters.get('statuses', [])
    if statuses:
        query['status'] = {'$in': statuses}
    
    # Verification status filter
    verification_statuses = filters.get('verification_statuses', [])
    if verification_statuses:
        query['verification_status'] = {'$in': verification_statuses}
    
    # Quality score filter
    min_quality = filters.get('min_quality_score')
    if min_quality is not None:
        query['data_quality_score'] = {'$gte': float(min_quality)}
    
    return query

def format_protest_for_export(protest: dict) -> dict:
    """Format protest data for export"""
    try:
        return {
            'id': str(protest['_id']),
            'title': protest.get('title', ''),
            'description': protest.get('description', ''),
            'location_description': protest.get('location_description', ''),
            'coordinates_latitude': protest.get('location', {}).get('coordinates', [0, 0])[1],
            'coordinates_longitude': protest.get('location', {}).get('coordinates', [0, 0])[0],
            'start_date': protest.get('start_date').isoformat() if protest.get('start_date') else '',
            'end_date': protest.get('end_date').isoformat() if protest.get('end_date') else '',
            'categories': ', '.join(protest.get('categories', [])),
            'organizers': ', '.join(protest.get('organizers', [])),
            'status': protest.get('status', ''),
            'verification_status': protest.get('verification_status', ''),
            'data_quality_score': protest.get('data_quality_score', 0),
            'trending_score': protest.get('trending_score', 0),
            'data_sources': ', '.join(protest.get('data_sources', [])),
            'external_links': ', '.join(protest.get('external_links', [])),
            'created_at': protest.get('created_at').isoformat() if protest.get('created_at') else '',
            'updated_at': protest.get('updated_at').isoformat() if protest.get('updated_at') else '',
            'views': protest.get('engagement_metrics', {}).get('views', 0),
            'shares': protest.get('engagement_metrics', {}).get('shares', 0),
            'bookmarks': protest.get('engagement_metrics', {}).get('bookmarks', 0)
        }
    except Exception as e:
        logger.error(f"Error formatting protest for export: {e}")
        return {}

def format_user_report_for_export(report: dict) -> dict:
    """Format user report for export"""
    try:
        return {
            'id': str(report['_id']),
            'title': report.get('content', {}).get('title', ''),
            'description': report.get('content', {}).get('description', ''),
            'location': report.get('content', {}).get('location', ''),
            'coordinates_latitude': report.get('location', {}).get('coordinates', [0, 0])[1],
            'coordinates_longitude': report.get('location', {}).get('coordinates', [0, 0])[0],
            'tags': ', '.join(report.get('tags', [])),
            'verification_status': report.get('verification_status', ''),
            'priority_level': report.get('priority_level', ''),
            'credibility_score': report.get('credibility_score', 0),
            'created_at': report.get('created_at').isoformat() if report.get('created_at') else '',
            'updated_at': report.get('updated_at').isoformat() if report.get('updated_at') else ''
        }
    except Exception as e:
        logger.error(f"Error formatting user report for export: {e}")
        return {}

def export_to_csv(data: list, filename: str) -> str:
    """Export data to CSV file"""
    try:
        if not data:
            return None
        
        # Create exports directory if it doesn't exist
        exports_dir = os.path.join(current_app.root_path, 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        file_path = os.path.join(exports_dir, filename)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        return file_path
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return None

def export_to_json(data: list, filename: str) -> str:
    """Export data to JSON file"""
    try:
        # Create exports directory if it doesn't exist
        exports_dir = os.path.join(current_app.root_path, 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        file_path = os.path.join(exports_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump({
                'export_metadata': {
                    'exported_at': datetime.utcnow().isoformat(),
                    'record_count': len(data),
                    'format': 'json'
                },
                'data': data
            }, jsonfile, indent=2, ensure_ascii=False)
        
        return file_path
        
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        return None

def process_export_request(request_id: str):
    """Process export request in background"""
    try:
        export_req = export_requests.get(request_id)
        if not export_req:
            return
        
        # Update status
        export_req.status = 'processing'
        export_req.started_at = datetime.utcnow()
        
        # Get user limits
        user = users_model.find_one({'_id': ObjectId(export_req.user_id)})
        if not user:
            export_req.status = 'failed'
            export_req.error_message = 'User not found'
            return
        
        user_type = user.get('user_type_id', 'citizen')
        limits = get_export_limits(user_type)
        max_records = limits['max_records']
        
        # Build query
        query = build_export_query(export_req.filters, export_req.export_type)
        
        # Get data based on export type
        if export_req.export_type == 'protests':
            # Get protests
            limit = max_records if max_records != -1 else None
            protests = list(protest_model.find_many(
                query,
                sort=[('created_at', -1)],
                limit=limit
            ))
            
            # Format for export
            formatted_data = [format_protest_for_export(protest) for protest in protests]
            
        elif export_req.export_type == 'user_reports':
            # Only export user's own reports
            query['user_id'] = ObjectId(export_req.user_id)
            
            limit = max_records if max_records != -1 else None
            reports = list(user_reports_model.find_many(
                query,
                sort=[('created_at', -1)],
                limit=limit
            ))
            
            # Format for export
            formatted_data = [format_user_report_for_export(report) for report in reports]
            
        elif export_req.export_type == 'user_bookmarks':
            # Export user's bookmarks with protest details
            query['user_id'] = ObjectId(export_req.user_id)
            
            bookmarks = list(bookmarks_model.find_many(query, sort=[('created_at', -1)]))
            
            # Get protest details for each bookmark
            formatted_data = []
            for bookmark in bookmarks:
                protest = protest_model.find_one({'_id': bookmark['protest_id']})
                if protest:
                    bookmark_data = {
                        'bookmark_id': str(bookmark['_id']),
                        'bookmark_created_at': bookmark.get('created_at').isoformat() if bookmark.get('created_at') else '',
                        'bookmark_notes': bookmark.get('notes', ''),
                        'bookmark_tags': ', '.join(bookmark.get('tags', [])),
                        'is_favorite': bookmark.get('is_favorite', False),
                        **format_protest_for_export(protest)
                    }
                    formatted_data.append(bookmark_data)
        
        else:
            export_req.status = 'failed'
            export_req.error_message = f'Unknown export type: {export_req.export_type}'
            return
        
        if not formatted_data:
            export_req.status = 'completed'
            export_req.error_message = 'No data found matching the specified criteria'
            export_req.completed_at = datetime.utcnow()
            return
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{export_req.export_type}_{export_req.user_id}_{timestamp}.{export_req.format_type}"
        
        # Export to file
        if export_req.format_type == 'csv':
            file_path = export_to_csv(formatted_data, filename)
        elif export_req.format_type == 'json':
            file_path = export_to_json(formatted_data, filename)
        else:
            export_req.status = 'failed'
            export_req.error_message = f'Unsupported format: {export_req.format_type}'
            return
        
        if file_path:
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Update export request
            export_req.status = 'completed'
            export_req.completed_at = datetime.utcnow()
            export_req.file_path = file_path
            export_req.file_size = file_size
            export_req.record_count = len(formatted_data)
            
            logger.info(f"Export completed: {request_id}, {len(formatted_data)} records, {file_size} bytes")
        else:
            export_req.status = 'failed'
            export_req.error_message = 'Failed to create export file'
        
    except Exception as e:
        logger.error(f"Export processing error: {e}")
        export_req = export_requests.get(request_id)
        if export_req:
            export_req.status = 'failed'
            export_req.error_message = str(e)
        
        error_log_model.log_error(
            service_name="export_service",
            error_type="export_processing_error",
            error_message=str(e),
            context={'request_id': request_id},
            severity="medium"
        )


# =====================================================
# EXPORT ENDPOINTS
# =====================================================

@bp.route('/export/csv', methods=['POST'])
@auth_required()
def export_csv():
    """Export data as CSV"""
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
        
        export_type = data.get('export_type')
        if not export_type:
            return jsonify({
                'success': False,
                'error': 'Missing export type',
                'message': 'export_type is required'
            }), 400
        
        valid_types = ['protests', 'user_reports', 'user_bookmarks']
        if export_type not in valid_types:
            return jsonify({
                'success': False,
                'error': 'Invalid export type',
                'message': f'export_type must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Check export limits
        can_export, limit_error = check_export_limits(user_id, user_type)
        if not can_export:
            return jsonify({
                'success': False,
                'error': 'Export limit exceeded',
                'message': limit_error
            }), 429
        
        # Validate filters
        filters = data.get('filters', {})
        valid_filters, filter_errors = validate_export_filters(filters, export_type)
        if not valid_filters:
            return jsonify({
                'success': False,
                'error': 'Invalid filters',
                'message': 'Filter validation failed',
                'details': filter_errors
            }), 400
        
        # Check format support
        limits = get_export_limits(user_type)
        if 'csv' not in limits['formats']:
            return jsonify({
                'success': False,
                'error': 'Format not supported',
                'message': 'CSV export is not available for your account type'
            }), 403
        
        # Create export request
        request_id = str(uuid.uuid4())
        export_req = ExportRequest(
            request_id=request_id,
            user_id=user_id,
            export_type=export_type,
            filters=filters,
            format_type='csv'
        )
        
        export_requests[request_id] = export_req
        
        # Start background processing
        thread = threading.Thread(target=process_export_request, args=(request_id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"CSV export requested by user {request.current_user['username']}: {export_type}")
        
        return jsonify({
            'success': True,
            'message': 'Export request created successfully',
            'data': {
                'request_id': request_id,
                'export_type': export_type,
                'format': 'csv',
                'status': 'queued',
                'estimated_completion': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                'max_records': limits['max_records'] if limits['max_records'] != -1 else 'unlimited'
            }
        }), 202
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        error_log_model.log_error(
            service_name="export_service",
            error_type="csv_export_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Export failed',
            'message': 'An error occurred while creating the export'
        }), 500


@bp.route('/export/json', methods=['POST'])
@auth_required()
def export_json():
    """Export data as JSON"""
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
        
        export_type = data.get('export_type')
        if not export_type:
            return jsonify({
                'success': False,
                'error': 'Missing export type',
                'message': 'export_type is required'
            }), 400
        
        valid_types = ['protests', 'user_reports', 'user_bookmarks']
        if export_type not in valid_types:
            return jsonify({
                'success': False,
                'error': 'Invalid export type',
                'message': f'export_type must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Check export limits
        can_export, limit_error = check_export_limits(user_id, user_type)
        if not can_export:
            return jsonify({
                'success': False,
                'error': 'Export limit exceeded',
                'message': limit_error
            }), 429
        
        # Validate filters
        filters = data.get('filters', {})
        valid_filters, filter_errors = validate_export_filters(filters, export_type)
        if not valid_filters:
            return jsonify({
                'success': False,
                'error': 'Invalid filters',
                'message': 'Filter validation failed',
                'details': filter_errors
            }), 400
        
        # Check format support
        limits = get_export_limits(user_type)
        if 'json' not in limits['formats']:
            return jsonify({
                'success': False,
                'error': 'Format not supported',
                'message': 'JSON export is not available for your account type'
            }), 403
        
        # Create export request
        request_id = str(uuid.uuid4())
        export_req = ExportRequest(
            request_id=request_id,
            user_id=user_id,
            export_type=export_type,
            filters=filters,
            format_type='json'
        )
        
        export_requests[request_id] = export_req
        
        # Start background processing
        thread = threading.Thread(target=process_export_request, args=(request_id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"JSON export requested by user {request.current_user['username']}: {export_type}")
        
        return jsonify({
            'success': True,
            'message': 'Export request created successfully',
            'data': {
                'request_id': request_id,
                'export_type': export_type,
                'format': 'json',
                'status': 'queued',
                'estimated_completion': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                'max_records': limits['max_records'] if limits['max_records'] != -1 else 'unlimited'
            }
        }), 202
        
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        error_log_model.log_error(
            service_name="export_service",
            error_type="json_export_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Export failed',
            'message': 'An error occurred while creating the export'
        }), 500


@bp.route('/export/status/<request_id>', methods=['GET'])
@auth_required()
def get_export_status(request_id):
    """Get export request status"""
    try:
        user_id = request.current_user['id']
        
        export_req = export_requests.get(request_id)
        if not export_req:
            return jsonify({
                'success': False,
                'error': 'Export request not found',
                'message': 'The specified export request could not be found'
            }), 404
        
        # Check if user owns this export request
        if export_req.user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You can only view your own export requests'
            }), 403
        
        # Build status response
        status_data = {
            'request_id': request_id,
            'export_type': export_req.export_type,
            'format': export_req.format_type,
            'status': export_req.status,
            'created_at': export_req.created_at.isoformat(),
            'started_at': export_req.started_at.isoformat() if export_req.started_at else None,
            'completed_at': export_req.completed_at.isoformat() if export_req.completed_at else None,
            'expires_at': export_req.expires_at.isoformat(),
            'record_count': export_req.record_count,
            'file_size_bytes': export_req.file_size,
            'download_count': export_req.download_count,
            'error_message': export_req.error_message
        }
        
        # Add download URL if completed
        if export_req.status == 'completed' and export_req.file_path:
            status_data['download_url'] = f'/api/export/download/{request_id}'
        
        # Add progress estimation for processing requests
        if export_req.status == 'processing' and export_req.started_at:
            elapsed = (datetime.utcnow() - export_req.started_at).total_seconds()
            estimated_total = 300  # 5 minutes estimated
            progress = min(90, (elapsed / estimated_total) * 100)  # Cap at 90% until actually complete
            status_data['progress_percentage'] = round(progress, 1)
        
        return jsonify({
            'success': True,
            'message': 'Export status retrieved successfully',
            'data': status_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get export status error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve export status',
            'message': 'An error occurred while retrieving export status'
        }), 500


@bp.route('/export/download/<request_id>', methods=['GET'])
@auth_required()
def download_export(request_id):
    """Download completed export file"""
    try:
        user_id = request.current_user['id']
        
        export_req = export_requests.get(request_id)
        if not export_req:
            return jsonify({
                'success': False,
                'error': 'Export request not found',
                'message': 'The specified export request could not be found'
            }), 404
        
        # Check if user owns this export request
        if export_req.user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You can only download your own exports'
            }), 403
        
        # Check if export is completed
        if export_req.status != 'completed':
            return jsonify({
                'success': False,
                'error': 'Export not ready',
                'message': f'Export status is "{export_req.status}". Download is only available for completed exports.'
            }), 400
        
        # Check if file exists
        if not export_req.file_path or not os.path.exists(export_req.file_path):
            return jsonify({
                'success': False,
                'error': 'File not found',
                'message': 'Export file is no longer available'
            }), 404
        
        # Check if expired
        if datetime.utcnow() > export_req.expires_at:
            return jsonify({
                'success': False,
                'error': 'Export expired',
                'message': 'This export has expired and is no longer available for download'
            }), 410
        
        # Increment download count
        export_req.download_count += 1
        
        # Get filename for download
        filename = os.path.basename(export_req.file_path)
        
        logger.info(f"Export downloaded by user {request.current_user['username']}: {request_id}")
        
        # Send file
        return send_file(
            export_req.file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Download export error: {e}")
        return jsonify({
            'success': False,
            'error': 'Download failed',
            'message': 'An error occurred while downloading the export'
        }), 500


@bp.route('/export/history', methods=['GET'])
@auth_required()
def get_export_history():
    """Get user's export history"""
    try:
        user_id = request.current_user['id']
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Get user's export requests
        user_exports = [
            req for req in export_requests.values()
            if req.user_id == user_id
        ]
        
        # Sort by creation date (newest first)
        user_exports.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        paginated_exports = user_exports[offset:offset + limit]
        
        # Format export history
        export_history = []
        for export_req in paginated_exports:
            history_item = {
                'request_id': export_req.request_id,
                'export_type': export_req.export_type,
                'format': export_req.format_type,
                'status': export_req.status,
                'created_at': export_req.created_at.isoformat(),
                'completed_at': export_req.completed_at.isoformat() if export_req.completed_at else None,
                'expires_at': export_req.expires_at.isoformat(),
                'record_count': export_req.record_count,
                'file_size_bytes': export_req.file_size,
                'download_count': export_req.download_count,
                'filters_applied': export_req.filters,
                'is_expired': datetime.utcnow() > export_req.expires_at,
                'is_downloadable': (
                    export_req.status == 'completed' and 
                    export_req.file_path and 
                    os.path.exists(export_req.file_path) and
                    datetime.utcnow() <= export_req.expires_at
                )
            }
            
            # Add download URL if available
            if history_item['is_downloadable']:
                history_item['download_url'] = f'/api/export/download/{export_req.request_id}'
            
            export_history.append(history_item)
        
        # Calculate pagination info
        total_count = len(user_exports)
        total_pages = (total_count + limit - 1) // limit
        
        # Calculate summary statistics
        summary = {
            'total_exports': total_count,
            'completed_exports': len([req for req in user_exports if req.status == 'completed']),
            'failed_exports': len([req for req in user_exports if req.status == 'failed']),
            'total_records_exported': sum(req.record_count for req in user_exports if req.status == 'completed'),
            'total_file_size_bytes': sum(req.file_size for req in user_exports if req.status == 'completed')
        }
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(export_history)} export history items',
            'data': {
                'export_history': export_history,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'summary': summary
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get export history error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve export history',
            'message': 'An error occurred while retrieving export history'
        }), 500


@bp.route('/export/limits', methods=['GET'])
@auth_required()
def get_export_limits_info():
    """Get user's export limits and usage"""
    try:
        user_id = request.current_user['id']
        user_type = request.current_user['user_type']
        
        # Get limits for user type
        limits = get_export_limits(user_type)
        
        # Count today's exports
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_exports = [
            req for req in export_requests.values()
            if req.user_id == user_id and req.created_at >= today
        ]
        
        # Calculate usage
        daily_usage = len(today_exports)
        daily_limit = limits['max_exports_per_day']
        
        usage_info = {
            'user_type': user_type,
            'limits': {
                'max_records_per_export': limits['max_records'],
                'max_exports_per_day': daily_limit,
                'supported_formats': limits['formats']
            },
            'current_usage': {
                'exports_today': daily_usage,
                'exports_remaining_today': max(0, daily_limit - daily_usage) if daily_limit != -1 else 'unlimited'
            },
            'can_export': daily_limit == -1 or daily_usage < daily_limit
        }
        
        return jsonify({
            'success': True,
            'message': 'Export limits information retrieved successfully',
            'data': usage_info
        }), 200
        
    except Exception as e:
        logger.error(f"Get export limits error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve export limits',
            'message': 'An error occurred while retrieving export limits'
        }), 500


@bp.route('/export/cancel/<request_id>', methods=['DELETE'])
@auth_required()
def cancel_export(request_id):
    """Cancel a queued or processing export request"""
    try:
        user_id = request.current_user['id']
        
        export_req = export_requests.get(request_id)
        if not export_req:
            return jsonify({
                'success': False,
                'error': 'Export request not found',
                'message': 'The specified export request could not be found'
            }), 404
        
        # Check if user owns this export request
        if export_req.user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You can only cancel your own export requests'
            }), 403
        
        # Check if export can be cancelled
        if export_req.status in ['completed', 'failed', 'cancelled']:
            return jsonify({
                'success': False,
                'error': 'Cannot cancel export',
                'message': f'Export with status "{export_req.status}" cannot be cancelled'
            }), 400
        
        # Cancel the export
        export_req.status = 'cancelled'
        export_req.completed_at = datetime.utcnow()
        export_req.error_message = 'Cancelled by user'
        
        # Clean up any partial files
        if export_req.file_path and os.path.exists(export_req.file_path):
            try:
                os.remove(export_req.file_path)
            except Exception as e:
                logger.warning(f"Failed to remove cancelled export file: {e}")
        
        logger.info(f"Export cancelled by user {request.current_user['username']}: {request_id}")
        
        return jsonify({
            'success': True,
            'message': 'Export request cancelled successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Cancel export error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to cancel export',
            'message': 'An error occurred while cancelling the export'
        }), 500


# =====================================================
# CLEANUP UTILITIES
# =====================================================

def cleanup_expired_exports():
    """Clean up expired export files and requests"""
    try:
        current_time = datetime.utcnow()
        expired_requests = []
        
        for request_id, export_req in export_requests.items():
            if current_time > export_req.expires_at:
                # Remove file if it exists
                if export_req.file_path and os.path.exists(export_req.file_path):
                    try:
                        os.remove(export_req.file_path)
                        logger.info(f"Removed expired export file: {export_req.file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove expired file: {e}")
                
                expired_requests.append(request_id)
        
        # Remove expired requests from memory
        for request_id in expired_requests:
            del export_requests[request_id]
        
        logger.info(f"Cleaned up {len(expired_requests)} expired export requests")
        
    except Exception as e:
        logger.error(f"Cleanup expired exports error: {e}")


@bp.route('/export/cleanup', methods=['POST'])
@auth_required(allowed_roles=['admin', 'moderator'])
def manual_cleanup():
    """Manually trigger cleanup of expired exports (admin only)"""
    try:
        cleanup_expired_exports()
        
        return jsonify({
            'success': True,
            'message': 'Export cleanup completed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Manual cleanup error: {e}")
        return jsonify({
            'success': False,
            'error': 'Cleanup failed',
            'message': 'An error occurred during cleanup'
        }), 500


# =====================================================
# PLACEHOLDER FOR EMAIL NOTIFICATIONS
# =====================================================

def send_export_notification(user_email: str, export_req: ExportRequest):
    """Send email notification when export is ready (placeholder)"""
    try:
        # TODO: Implement email notification when email service is configured
        logger.info(f"Email notification placeholder: Export {export_req.request_id} ready for {user_email}")
        
        # In production, you would:
        # 1. Use an email service (SendGrid, SES, etc.)
        # 2. Send an email with download link
        # 3. Include export details and expiration info
        
        pass
        
    except Exception as e:
        logger.error(f"Email notification error: {e}")


# =====================================================
# HEALTH CHECK
# =====================================================

@bp.route('/export/health', methods=['GET'])
def export_health_check():
    """Export service health check"""
    try:
        # Check export directory
        exports_dir = os.path.join(current_app.root_path, 'exports')
        exports_dir_exists = os.path.exists(exports_dir)
        
        # Count active requests
        active_requests = len([req for req in export_requests.values() if req.status in ['queued', 'processing']])
        completed_requests = len([req for req in export_requests.values() if req.status == 'completed'])
        failed_requests = len([req for req in export_requests.values() if req.status == 'failed'])
        
        # Check disk space (simplified)
        import shutil
        if exports_dir_exists:
            total, used, free = shutil.disk_usage(exports_dir)
            disk_usage_percent = (used / total) * 100
        else:
            disk_usage_percent = 0
        
        return jsonify({
            'success': True,
            'message': 'Export service is healthy',
            'data': {
                'service': 'export_service',
                'status': 'healthy',
                'exports_directory_exists': exports_dir_exists,
                'active_requests': active_requests,
                'completed_requests': completed_requests,
                'failed_requests': failed_requests,
                'total_requests': len(export_requests),
                'disk_usage_percent': round(disk_usage_percent, 1),
                'features': {
                    'csv_export': True,
                    'json_export': True,
                    'background_processing': True,
                    'download_links': True,
                    'export_history': True,
                    'user_limits': True,
                    'automatic_cleanup': True,
                    'email_notifications': False  # Placeholder
                },
                'supported_export_types': [
                    'protests', 'user_reports', 'user_bookmarks'
                ],
                'supported_formats': ['csv', 'json']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Export health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Export service unhealthy',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['bp']