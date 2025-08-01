# blueprints/protests.py
"""
Enhanced Protests Blueprint - Core Protest Data & Discovery
- Public protest data (no auth required)
- Protest search and filtering
- Map data for frontend visualization  
- Trending and featured protests
- Categories and analytics
- Connects to enhanced data collector
"""

import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
import logging

# Initialize blueprint
bp = Blueprint('protests', __name__)
logger = logging.getLogger(__name__)

# Import auth decorator
try:
    from blueprints.auth import auth_required
except ImportError:
    # Mock decorator for development
    def auth_required(allowed_roles=None):
        def decorator(f):
            def decorated_function(*args, **kwargs):
                request.current_user = {'id': 'mock_user', 'user_type': 'citizen'}
                return f(*args, **kwargs)
            return decorated_function
        return decorator

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.data_collection_models import Protest, ProtestAnalytics
    from models.web_app_models import UserBookmarks, UserFollows
    from models.system_monitoring_models import ErrorLog
    from services.data_collector import get_enhanced_data_collector
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # Mock models for development
    class Protest:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def find_one(self, query): return None
        def count(self, query=None): return 0
        def get_recent_protests(self, **kwargs): return []
        def get_trending_protests(self, **kwargs): return []
        def get_featured_protests(self, **kwargs): return []
        def get_protests_by_category(self, **kwargs): return []
        def get_protests_near_location(self, **kwargs): return []
    
    class ProtestAnalytics:
        def __init__(self): pass
        def get_category_stats(self): return {}
        def get_geographic_stats(self): return {}
        def get_trending_categories(self): return []
    
    class UserBookmarks:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
    
    class UserFollows:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass
    
    def get_enhanced_data_collector():
        class MockCollector:
            def get_comprehensive_status(self): 
                return {'status': 'mock', 'total_protests': 0}
        return MockCollector()

# Initialize models
protest_model = Protest()
analytics_model = ProtestAnalytics()
bookmarks_model = UserBookmarks()
follows_model = UserFollows()
error_log_model = ErrorLog()


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def format_protest_data(protest, include_sensitive=False, user_context=None):
    """Format protest data for API response"""
    try:
        if not protest:
            return None
        
        # Basic protest information
        formatted = {
            'id': str(protest['_id']),
            'title': protest.get('title', ''),
            'description': protest.get('description', ''),
            'location': {
                'coordinates': protest.get('location', {}).get('coordinates', [0, 0]),
                'description': protest.get('location_description', ''),
                'country': protest.get('source_metadata', {}).get('country', ''),
                'geocoding_confidence': protest.get('geocoding_confidence', 0)
            },
            'dates': {
                'start_date': protest.get('start_date').isoformat() if protest.get('start_date') else None,
                'end_date': protest.get('end_date').isoformat() if protest.get('end_date') else None,
                'created_at': protest.get('created_at').isoformat() if protest.get('created_at') else None,
                'updated_at': protest.get('updated_at').isoformat() if protest.get('updated_at') else None
            },
            'categories': protest.get('categories', []),
            'organizers': protest.get('organizers', []),
            'status': protest.get('status', 'active'),
            'verification_status': protest.get('verification_status', 'unverified'),
            'data_quality_score': protest.get('data_quality_score', 0),
            'trending_score': protest.get('trending_score', 0),
            'featured': protest.get('featured', False),
            'visibility': protest.get('visibility', 'public'),
            'data_sources': protest.get('data_sources', []),
            'external_links': protest.get('external_links', []),
            'engagement_metrics': {
                'views': protest.get('engagement_metrics', {}).get('views', 0),
                'shares': protest.get('engagement_metrics', {}).get('shares', 0),
                'bookmarks': protest.get('engagement_metrics', {}).get('bookmarks', 0)
            }
        }
        
        # Add user-specific context if provided
        if user_context:
            formatted['user_context'] = {
                'is_bookmarked': user_context.get('is_bookmarked', False),
                'is_following': user_context.get('is_following', False),
                'user_can_edit': user_context.get('user_can_edit', False)
            }
        
        # Include sensitive data for admin/moderator users
        if include_sensitive:
            formatted['internal'] = {
                'content_hash': protest.get('content_hash', ''),
                'merge_count': protest.get('merge_count', 0),
                'source_metadata': protest.get('source_metadata', {}),
                'processing_notes': protest.get('processing_notes', [])
            }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting protest data: {e}")
        return None

def parse_query_filters(args):
    """Parse query parameters into database filters"""
    filters = {}
    
    try:
        # Date range filtering
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['$gte'] = datetime.fromisoformat(start_date.replace('Z', ''))
            if end_date:
                date_filter['$lte'] = datetime.fromisoformat(end_date.replace('Z', ''))
            filters['start_date'] = date_filter
        
        # Category filtering
        categories = args.getlist('categories')  # Handle multiple categories
        if categories:
            filters['categories'] = {'$in': categories}
        
        # Location filtering
        country = args.get('country')
        if country:
            filters['source_metadata.country'] = country
        
        # Status filtering
        status = args.get('status')
        if status:
            filters['status'] = status
        
        # Verification status filtering
        verification_status = args.get('verification_status')
        if verification_status:
            filters['verification_status'] = verification_status
        
        # Visibility filtering (always include for public API)
        filters['visibility'] = 'public'
        
        # Quality score filtering
        min_quality = args.get('min_quality_score', type=float)
        if min_quality is not None:
            filters['data_quality_score'] = {'$gte': min_quality}
        
        # Geographic bounding box
        bbox = args.get('bbox')  # Format: "west,south,east,north"
        if bbox:
            try:
                west, south, east, north = map(float, bbox.split(','))
                filters['location'] = {
                    '$geoWithin': {
                        '$box': [[west, south], [east, north]]
                    }
                }
            except ValueError:
                logger.warning(f"Invalid bbox format: {bbox}")
        
        return filters
        
    except Exception as e:
        logger.error(f"Error parsing query filters: {e}")
        return {'visibility': 'public'}  # Default filter

def parse_pagination(args):
    """Parse pagination parameters"""
    try:
        page = max(1, int(args.get('page', 1)))
        limit = min(100, max(1, int(args.get('limit', 20))))  # Max 100 items per page
        offset = (page - 1) * limit
        
        return {
            'page': page,
            'limit': limit,
            'offset': offset
        }
    except (ValueError, TypeError):
        return {'page': 1, 'limit': 20, 'offset': 0}

def parse_sorting(args):
    """Parse sorting parameters"""
    try:
        sort_by = args.get('sort', 'trending_score')
        sort_order = args.get('order', 'desc')
        
        valid_sort_fields = [
            'start_date', 'created_at', 'updated_at', 'trending_score',
            'data_quality_score', 'engagement_metrics.views', 'title'
        ]
        
        if sort_by not in valid_sort_fields:
            sort_by = 'trending_score'
        
        order = -1 if sort_order.lower() == 'desc' else 1
        
        return [(sort_by, order)]
        
    except Exception as e:
        logger.error(f"Error parsing sorting: {e}")
        return [('trending_score', -1)]


# =====================================================
# PUBLIC PROTEST ENDPOINTS (No Authentication Required)
# =====================================================

@bp.route('/protests', methods=['GET'])
def get_protests():
    """Get protests with filtering, pagination, and sorting"""
    try:
        # Parse query parameters
        filters = parse_query_filters(request.args)
        pagination = parse_pagination(request.args)
        sort_criteria = parse_sorting(request.args)
        
        # Search query
        search_query = request.args.get('q', '').strip()
        if search_query:
            # Add text search to filters
            filters['$text'] = {'$search': search_query}
        
        # Get protests from database
        protests = list(protest_model.find_many(
            filters,
            sort=sort_criteria,
            limit=pagination['limit'],
            skip=pagination['offset']
        ))
        
        # Get total count for pagination
        total_count = protest_model.count(filters)
        
        # Format protest data
        formatted_protests = []
        for protest in protests:
            formatted_protest = format_protest_data(protest)
            if formatted_protest:
                formatted_protests.append(formatted_protest)
        
        # Calculate pagination info
        total_pages = (total_count + pagination['limit'] - 1) // pagination['limit']
        has_next = pagination['page'] < total_pages
        has_prev = pagination['page'] > 1
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_protests)} protests',
            'data': {
                'protests': formatted_protests,
                'pagination': {
                    'current_page': pagination['page'],
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': pagination['limit'],
                    'has_next': has_next,
                    'has_prev': has_prev
                },
                'filters_applied': {
                    'search_query': search_query,
                    'categories': request.args.getlist('categories'),
                    'country': request.args.get('country'),
                    'date_range': {
                        'start': request.args.get('start_date'),
                        'end': request.args.get('end_date')
                    }
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get protests error: {e}")
        error_log_model.log_error(
            service_name="protests_api",
            error_type="get_protests_error",
            error_message=str(e),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve protests',
            'message': 'An error occurred while retrieving protests'
        }), 500


@bp.route('/protests/<protest_id>', methods=['GET'])
def get_protest_details(protest_id):
    """Get detailed information about a specific protest"""
    try:
        # Validate protest ID
        if not ObjectId.is_valid(protest_id):
            return jsonify({
                'success': False,
                'error': 'Invalid protest ID',
                'message': 'The provided protest ID is not valid'
            }), 400
        
        # Get protest from database
        protest = protest_model.find_one({
            '_id': ObjectId(protest_id),
            'visibility': 'public'
        })
        
        if not protest:
            return jsonify({
                'success': False,
                'error': 'Protest not found',
                'message': 'The requested protest could not be found'
            }), 404
        
        # Format protest data
        formatted_protest = format_protest_data(protest)
        
        if not formatted_protest:
            return jsonify({
                'success': False,
                'error': 'Data formatting error',
                'message': 'An error occurred while formatting protest data'
            }), 500
        
        # Increment view count (basic analytics)
        try:
            protest_model.update_by_id(protest['_id'], {
                '$inc': {'engagement_metrics.views': 1},
                '$set': {'last_viewed_at': datetime.utcnow()}
            })
        except Exception as e:
            logger.warning(f"Failed to update view count: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Protest details retrieved successfully',
            'data': {
                'protest': formatted_protest
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get protest details error: {e}")
        error_log_model.log_error(
            service_name="protests_api",
            error_type="get_protest_details_error",
            error_message=str(e),
            context={'protest_id': protest_id},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve protest details',
            'message': 'An error occurred while retrieving protest details'
        }), 500


@bp.route('/protests/map-data', methods=['GET'])
def get_map_data():
    """Get protest data optimized for map display"""
    try:
        # Parse filters (similar to get_protests but optimized for map)
        filters = parse_query_filters(request.args)
        
        # Limit results for map performance
        limit = min(1000, int(request.args.get('limit', 500)))
        
        # Only get essential fields for map markers
        projection = {
            'title': 1,
            'location': 1,
            'location_description': 1,
            'start_date': 1,
            'categories': 1,
            'status': 1,
            'verification_status': 1,
            'data_quality_score': 1,
            'trending_score': 1,
            'featured': 1
        }
        
        # Get protests for map
        protests = list(protest_model.find_many(
            filters,
            projection=projection,
            sort=[('trending_score', -1)],
            limit=limit
        ))
        
        # Format for map display
        map_markers = []
        for protest in protests:
            if protest.get('location', {}).get('coordinates', [0, 0]) != [0, 0]:
                marker = {
                    'id': str(protest['_id']),
                    'title': protest.get('title', ''),
                    'coordinates': protest.get('location', {}).get('coordinates', [0, 0]),
                    'location_description': protest.get('location_description', ''),
                    'categories': protest.get('categories', []),
                    'status': protest.get('status', 'active'),
                    'verification_status': protest.get('verification_status', 'unverified'),
                    'trending_score': protest.get('trending_score', 0),
                    'featured': protest.get('featured', False),
                    'start_date': protest.get('start_date').isoformat() if protest.get('start_date') else None
                }
                map_markers.append(marker)
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(map_markers)} map markers',
            'data': {
                'markers': map_markers,
                'total_markers': len(map_markers),
                'bounds': {
                    'note': 'Calculate bounds on frontend for better performance'
                },
                'clustering': {
                    'recommended': len(map_markers) > 100,
                    'zoom_threshold': 10
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get map data error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve map data',
            'message': 'An error occurred while retrieving map data'
        }), 500


@bp.route('/protests/trending', methods=['GET'])
def get_trending_protests():
    """Get trending protests"""
    try:
        limit = min(50, int(request.args.get('limit', 10)))
        
        # Get trending protests (high trending score, recent activity)
        trending_protests = list(protest_model.find_many(
            {
                'visibility': 'public',
                'status': {'$in': ['active', 'ongoing']},
                'trending_score': {'$gt': 0}
            },
            sort=[('trending_score', -1), ('start_date', -1)],
            limit=limit
        ))
        
        # Format protests
        formatted_protests = []
        for protest in trending_protests:
            formatted_protest = format_protest_data(protest)
            if formatted_protest:
                formatted_protests.append(formatted_protest)
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_protests)} trending protests',
            'data': {
                'trending_protests': formatted_protests,
                'generated_at': datetime.utcnow().isoformat(),
                'algorithm_note': 'Based on trending score, engagement, and recency'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get trending protests error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trending protests',
            'message': 'An error occurred while retrieving trending protests'
        }), 500


@bp.route('/protests/featured', methods=['GET'])
def get_featured_protests():
    """Get featured protests"""
    try:
        limit = min(20, int(request.args.get('limit', 10)))
        
        # Get featured protests
        featured_protests = list(protest_model.find_many(
            {
                'visibility': 'public',
                'featured': True,
                'status': {'$in': ['active', 'ongoing', 'completed']}
            },
            sort=[('trending_score', -1), ('start_date', -1)],
            limit=limit
        ))
        
        # Format protests
        formatted_protests = []
        for protest in featured_protests:
            formatted_protest = format_protest_data(protest)
            if formatted_protest:
                formatted_protests.append(formatted_protest)
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(formatted_protests)} featured protests',
            'data': {
                'featured_protests': formatted_protests,
                'note': 'Curated by editorial team for significance and quality'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get featured protests error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve featured protests',
            'message': 'An error occurred while retrieving featured protests'
        }), 500


@bp.route('/protests/categories', methods=['GET'])
def get_protest_categories():
    """Get available protest categories with counts"""
    try:
        # Get category statistics
        category_stats = analytics_model.get_category_stats()
        
        # Fallback if analytics model not available
        if not category_stats:
            # Get categories from recent protests
            pipeline = [
                {'$match': {'visibility': 'public'}},
                {'$unwind': '$categories'},
                {'$group': {
                    '_id': '$categories',
                    'count': {'$sum': 1},
                    'recent_count': {
                        '$sum': {
                            '$cond': [
                                {'$gte': ['$start_date', datetime.utcnow() - timedelta(days=30)]},
                                1, 0
                            ]
                        }
                    }
                }},
                {'$sort': {'count': -1}},
                {'$limit': 50}
            ]
            
            try:
                category_results = list(protest_model.collection.aggregate(pipeline))
                category_stats = {
                    result['_id']: {
                        'total_count': result['count'],
                        'recent_count': result['recent_count']
                    }
                    for result in category_results
                }
            except Exception:
                # Ultimate fallback
                category_stats = {
                    'Human Rights': {'total_count': 0, 'recent_count': 0},
                    'Environmental': {'total_count': 0, 'recent_count': 0},
                    'Labor Rights': {'total_count': 0, 'recent_count': 0},
                    'Political': {'total_count': 0, 'recent_count': 0},
                    'Social Justice': {'total_count': 0, 'recent_count': 0}
                }
        
        # Format categories
        categories = []
        for category, stats in category_stats.items():
            categories.append({
                'name': category,
                'slug': category.lower().replace(' ', '_'),
                'total_protests': stats.get('total_count', 0),
                'recent_protests': stats.get('recent_count', 0),
                'is_trending': stats.get('recent_count', 0) > 5
            })
        
        # Sort by total count
        categories.sort(key=lambda x: x['total_protests'], reverse=True)
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(categories)} categories',
            'data': {
                'categories': categories,
                'total_categories': len(categories),
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get categories error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve categories',
            'message': 'An error occurred while retrieving categories'
        }), 500


@bp.route('/protests/nearby', methods=['GET'])
def get_nearby_protests():
    """Get protests near a specific location"""
    try:
        # Get location parameters
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius_km = min(500, int(request.args.get('radius', 50)))  # Max 500km
        limit = min(100, int(request.args.get('limit', 20)))
        
        if lat is None or lng is None:
            return jsonify({
                'success': False,
                'error': 'Missing coordinates',
                'message': 'Latitude and longitude are required'
            }), 400
        
        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return jsonify({
                'success': False,
                'error': 'Invalid coordinates',
                'message': 'Latitude must be between -90 and 90, longitude between -180 and 180'
            }), 400
        
        # Build geo query
        geo_query = {
            'location': {
                '$geoWithin': {
                    '$centerSphere': [[lng, lat], radius_km / 6371]  # Earth radius in km
                }
            },
            'visibility': 'public'
        }
        
        # Get nearby protests
        nearby_protests = list(protest_model.find_many(
            geo_query,
            sort=[('trending_score', -1)],
            limit=limit
        ))
        
        # Format protests with distance calculation
        formatted_protests = []
        for protest in nearby_protests:
            formatted_protest = format_protest_data(protest)
            if formatted_protest:
                # Calculate approximate distance (simple haversine)
                protest_coords = protest.get('location', {}).get('coordinates', [0, 0])
                if protest_coords != [0, 0]:
                    # Simple distance calculation (not perfectly accurate but good enough)
                    from math import radians, cos, sin, asin, sqrt
                    
                    def haversine(lon1, lat1, lon2, lat2):
                        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                        dlon = lon2 - lon1
                        dlat = lat2 - lat1
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * asin(sqrt(a))
                        r = 6371  # Radius of earth in kilometers
                        return c * r
                    
                    distance = haversine(lng, lat, protest_coords[0], protest_coords[1])
                    formatted_protest['distance_km'] = round(distance, 2)
                
                formatted_protests.append(formatted_protest)
        
        # Sort by distance if calculated
        if formatted_protests and 'distance_km' in formatted_protests[0]:
            formatted_protests.sort(key=lambda x: x.get('distance_km', float('inf')))
        
        return jsonify({
            'success': True,
            'message': f'Found {len(formatted_protests)} protests within {radius_km}km',
            'data': {
                'protests': formatted_protests,
                'search_center': {'lat': lat, 'lng': lng},
                'search_radius_km': radius_km,
                'total_found': len(formatted_protests)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get nearby protests error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve nearby protests',
            'message': 'An error occurred while searching for nearby protests'
        }), 500


# =====================================================
# PROTEST ANALYTICS & STATISTICS
# =====================================================

@bp.route('/protests/analytics/overview', methods=['GET'])
def get_analytics_overview():
    """Get general protest analytics and statistics"""
    try:
        # Time range for analytics
        days = min(365, int(request.args.get('days', 30)))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic statistics
        total_protests = protest_model.count({'visibility': 'public'})
        recent_protests = protest_model.count({
            'visibility': 'public',
            'created_at': {'$gte': start_date}
        })
        active_protests = protest_model.count({
            'visibility': 'public',
            'status': {'$in': ['active', 'ongoing']}
        })
        
        # Category distribution
        category_stats = analytics_model.get_category_stats()
        
        # Geographic distribution
        geographic_stats = analytics_model.get_geographic_stats()
        
        # Trending categories
        trending_categories = analytics_model.get_trending_categories()
        
        return jsonify({
            'success': True,
            'message': 'Analytics overview retrieved successfully',
            'data': {
                'overview': {
                    'total_protests': total_protests,
                    'recent_protests': recent_protests,
                    'active_protests': active_protests,
                    'time_period_days': days
                },
                'category_distribution': category_stats or {},
                'geographic_distribution': geographic_stats or {},
                'trending_categories': trending_categories or [],
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get analytics overview error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve analytics',
            'message': 'An error occurred while retrieving analytics data'
        }), 500


# =====================================================
# DATA COLLECTION STATUS (Public)
# =====================================================

@bp.route('/protests/data-status', methods=['GET'])
def get_data_collection_status():
    """Get public information about data collection status"""
    try:
        # Get status from enhanced data collector
        collector = get_enhanced_data_collector()
        status = collector.get_comprehensive_status()
        
        # Format public-friendly status
        public_status = {
            'last_updated': status.get('health_status', {}).get('last_check', datetime.utcnow().isoformat()),
            'total_protests': status.get('database_statistics', {}).get('total_protests', 0),
            'data_sources_active': len([s for s in status.get('services_status', {}).values() if s]),
            'collection_status': 'active' if status.get('is_collecting') else 'idle',
            'data_quality': {
                'average_quality_score': 0.75,  # TODO: Calculate from real data
                'verified_protests': status.get('database_statistics', {}).get('total_protests', 0) * 0.6,  # Estimate
                'last_collection': status.get('health_status', {}).get('last_check', datetime.utcnow().isoformat())
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'Data collection status retrieved successfully',
            'data': public_status
        }), 200
        
    except Exception as e:
        logger.error(f"Get data status error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve data status',
            'message': 'An error occurred while retrieving data collection status'
        }), 500


# =====================================================
# HEALTH CHECK
# =====================================================

@bp.route('/protests/health', methods=['GET'])
def protests_health_check():
    """Protests service health check"""
    try:
        # Test database connectivity
        test_count = protest_model.count()
        
        # Test enhanced data collector connection
        try:
            collector = get_enhanced_data_collector()
            collector_status = collector.get_comprehensive_status()
            collector_healthy = True
        except Exception:
            collector_healthy = False
            collector_status = {}
        
        return jsonify({
            'success': True,
            'message': 'Protests service is healthy',
            'data': {
                'service': 'protests_api',
                'status': 'healthy',
                'database_connected': True,
                'total_protests': test_count,
                'data_collector_connected': collector_healthy,
                'features': {
                    'public_protests': True,
                    'search_filtering': True,
                    'map_data': True,
                    'trending_protests': True,
                    'featured_protests': True,
                    'categories': True,
                    'nearby_search': True,
                    'analytics': True
                },
                'collector_status': {
                    'available': collector_healthy,
                    'last_collection': collector_status.get('health_status', {}).get('last_check')
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Protests health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Protests service unhealthy',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['bp']