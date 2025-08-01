# blueprints/analytics.py
"""
Analytics Blueprint - Analytics & Research Data
- Personal user analytics and statistics
- Protest trends and patterns analysis
- Geographic analysis and mapping data
- Category-based analytics
- Time-series analysis
- Research-grade data insights
- Custom analytics queries
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
import logging
import calendar

# Initialize blueprint
bp = Blueprint('analytics', __name__)
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
    from models.data_collection_models import Protest, ProtestAnalytics
    from models.web_app_models import UserReports, Posts, Users, UserBookmarks, UserFollows
    from models.system_monitoring_models import ErrorLog
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # Mock models for development
    class Protest:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
        def collection(self):
            class MockCollection:
                def aggregate(self, pipeline): return []
            return MockCollection()
    
    class ProtestAnalytics:
        def __init__(self): pass
        def get_category_stats(self): return {}
        def get_geographic_stats(self): return {}
        def get_trending_categories(self): return []
    
    class UserReports:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
        def collection(self):
            class MockCollection:
                def aggregate(self, pipeline): return []
            return MockCollection()
    
    class Posts:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
        def collection(self):
            class MockCollection:
                def aggregate(self, pipeline): return []
            return MockCollection()
    
    class Users:
        def __init__(self): pass
        def find_one(self, query): return None
        def count(self, query=None): return 0
        def collection(self):
            class MockCollection:
                def aggregate(self, pipeline): return []
            return MockCollection()
    
    class UserBookmarks:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
        def collection(self):
            class MockCollection:
                def aggregate(self, pipeline): return []
            return MockCollection()
    
    class UserFollows:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass

# Initialize models
protest_model = Protest()
protest_analytics_model = ProtestAnalytics()
user_reports_model = UserReports()
posts_model = Posts()
users_model = Users()
bookmarks_model = UserBookmarks()
follows_model = UserFollows()
error_log_model = ErrorLog()


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def get_date_range(period: str) -> tuple:
    """Get start and end dates for common periods"""
    end_date = datetime.utcnow()
    
    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    elif period == '90d':
        start_date = end_date - timedelta(days=90)
    elif period == '1y':
        start_date = end_date - timedelta(days=365)
    elif period == 'ytd':
        start_date = datetime(end_date.year, 1, 1)
    elif period == 'all':
        start_date = datetime(2020, 1, 1)  # Reasonable start date
    else:
        start_date = end_date - timedelta(days=30)  # Default to 30 days
    
    return start_date, end_date

def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, returning default if denominator is 0"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def calculate_growth_rate(current, previous):
    """Calculate growth rate between two values"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100

def aggregate_with_fallback(collection, pipeline, fallback_value=None):
    """Run aggregation with fallback for mock collections"""
    try:
        return list(collection.aggregate(pipeline))
    except Exception as e:
        logger.warning(f"Aggregation failed, using fallback: {e}")
        return fallback_value or []


# =====================================================
# PERSONAL ANALYTICS ENDPOINTS
# =====================================================

@bp.route('/analytics/personal', methods=['GET'])
@auth_required()
def get_personal_analytics():
    """Get personal analytics for the authenticated user"""
    try:
        user_id = request.current_user['id']
        period = request.args.get('period', '30d')
        
        start_date, end_date = get_date_range(period)
        
        # Get user info
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Calculate account age
        account_created = user.get('created_at', datetime.utcnow())
        account_age_days = (datetime.utcnow() - account_created).days
        
        # Basic user statistics
        basic_stats = {
            'reports_submitted': user_reports_model.count({'user_id': ObjectId(user_id)}),
            'posts_created': posts_model.count({'user_id': ObjectId(user_id)}),
            'protests_bookmarked': bookmarks_model.count({'user_id': ObjectId(user_id)}),
            'protests_following': follows_model.count({'user_id': ObjectId(user_id), 'active': True}),
            'account_age_days': account_age_days
        }
        
        # Activity over time (last 30 days)
        activity_pipeline = [
            {
                '$match': {
                    'user_id': ObjectId(user_id),
                    'created_at': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$created_at'
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        # Get activity from reports
        reports_activity = aggregate_with_fallback(
            user_reports_model.collection, 
            activity_pipeline, 
            []
        )
        
        # Get activity from posts
        posts_activity = aggregate_with_fallback(
            posts_model.collection, 
            activity_pipeline, 
            []
        )
        
        # Combine activity data
        activity_by_date = {}
        for item in reports_activity:
            date_str = item['_id']
            activity_by_date[date_str] = activity_by_date.get(date_str, 0) + item['count']
        
        for item in posts_activity:
            date_str = item['_id']
            activity_by_date[date_str] = activity_by_date.get(date_str, 0) + item['count']
        
        # Format activity timeline
        activity_timeline = [
            {'date': date, 'activity_count': count}
            for date, count in sorted(activity_by_date.items())
        ]
        
        # Category interests (based on bookmarks and follows)
        bookmark_categories = []
        try:
            # Get categories from bookmarked protests
            bookmark_pipeline = [
                {'$match': {'user_id': ObjectId(user_id)}},
                {
                    '$lookup': {
                        'from': 'protests',
                        'localField': 'protest_id',
                        'foreignField': '_id',
                        'as': 'protest'
                    }
                },
                {'$unwind': '$protest'},
                {'$unwind': '$protest.categories'},
                {
                    '$group': {
                        '_id': '$protest.categories',
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            
            bookmark_categories = aggregate_with_fallback(
                bookmarks_model.collection, 
                bookmark_pipeline, 
                []
            )
        except Exception as e:
            logger.warning(f"Bookmark categories aggregation failed: {e}")
        
        # Format category interests
        category_interests = [
            {
                'category': item['_id'],
                'interaction_count': item['count'],
                'interaction_type': 'bookmark'
            }
            for item in bookmark_categories
        ]
        
        # Engagement levels
        total_interactions = (
            basic_stats['reports_submitted'] + 
            basic_stats['posts_created'] + 
            basic_stats['protests_bookmarked'] + 
            basic_stats['protests_following']
        )
        
        if total_interactions >= 50:
            engagement_level = 'high'
        elif total_interactions >= 15:
            engagement_level = 'medium'
        elif total_interactions >= 5:
            engagement_level = 'low'
        else:
            engagement_level = 'minimal'
        
        # Calculate activity score
        activity_score = min(100, (
            basic_stats['reports_submitted'] * 5 +
            basic_stats['posts_created'] * 3 +
            basic_stats['protests_bookmarked'] * 1 +
            basic_stats['protests_following'] * 2
        ))
        
        # Recent activity summary
        recent_reports = user_reports_model.count({
            'user_id': ObjectId(user_id),
            'created_at': {'$gte': start_date}
        })
        
        recent_posts = posts_model.count({
            'user_id': ObjectId(user_id),
            'created_at': {'$gte': start_date}
        })
        
        recent_activity = {
            'reports_submitted': recent_reports,
            'posts_created': recent_posts,
            'total_recent_actions': recent_reports + recent_posts
        }
        
        return jsonify({
            'success': True,
            'message': 'Personal analytics retrieved successfully',
            'data': {
                'user_info': {
                    'user_id': user_id,
                    'username': user.get('username', ''),
                    'user_type': user.get('user_type_id', 'citizen'),
                    'account_created': account_created.isoformat() if account_created else None,
                    'account_age_days': account_age_days
                },
                'overall_statistics': basic_stats,
                'recent_activity': recent_activity,
                'activity_timeline': activity_timeline,
                'category_interests': category_interests,
                'engagement': {
                    'level': engagement_level,
                    'score': activity_score,
                    'total_interactions': total_interactions
                },
                'period': {
                    'selected': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Personal analytics error: {e}")
        error_log_model.log_error(
            service_name="analytics_service",
            error_type="personal_analytics_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve personal analytics',
            'message': 'An error occurred while retrieving your analytics'
        }), 500


# =====================================================
# PROTEST TRENDS ENDPOINTS
# =====================================================

@bp.route('/analytics/protests/trends', methods=['GET'])
def get_protest_trends():
    """Get protest trends and patterns analysis"""
    try:
        period = request.args.get('period', '30d')
        granularity = request.args.get('granularity', 'daily')  # daily, weekly, monthly
        
        start_date, end_date = get_date_range(period)
        
        # Determine date format based on granularity
        if granularity == 'monthly':
            date_format = '%Y-%m'
        elif granularity == 'weekly':
            date_format = '%Y-W%U'  # Year-Week
        else:  # daily
            date_format = '%Y-%m-%d'
        
        # Protests over time
        time_series_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': date_format,
                            'date': '$start_date'
                        }
                    },
                    'protest_count': {'$sum': 1},
                    'avg_quality_score': {'$avg': '$data_quality_score'},
                    'verified_count': {
                        '$sum': {
                            '$cond': [
                                {'$eq': ['$verification_status', 'verified']}, 
                                1, 0
                            ]
                        }
                    }
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        time_series_data = aggregate_with_fallback(
            protest_model.collection, 
            time_series_pipeline, 
            []
        )
        
        # Category trends
        category_trends_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {'$unwind': '$categories'},
            {
                '$group': {
                    '_id': {
                        'category': '$categories',
                        'period': {
                            '$dateToString': {
                                'format': date_format,
                                'date': '$start_date'
                            }
                        }
                    },
                    'count': {'$sum': 1},
                    'avg_trending_score': {'$avg': '$trending_score'}
                }
            },
            {'$sort': {'_id.period': 1, 'count': -1}}
        ]
        
        category_trends_data = aggregate_with_fallback(
            protest_model.collection, 
            category_trends_pipeline, 
            []
        )
        
        # Geographic distribution trends
        geographic_trends_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': {
                        'country': '$source_metadata.country',
                        'period': {
                            '$dateToString': {
                                'format': date_format,
                                'date': '$start_date'
                            }
                        }
                    },
                    'count': {'$sum': 1},
                    'avg_quality': {'$avg': '$data_quality_score'}
                }
            },
            {'$match': {'_id.country': {'$ne': None, '$ne': ''}}},
            {'$sort': {'_id.period': 1, 'count': -1}}
        ]
        
        geographic_trends_data = aggregate_with_fallback(
            protest_model.collection, 
            geographic_trends_pipeline, 
            []
        )
        
        # Calculate growth rates for time series
        formatted_time_series = []
        previous_count = 0
        
        for item in time_series_data:
            current_count = item['protest_count']
            growth_rate = calculate_growth_rate(current_count, previous_count)
            
            formatted_time_series.append({
                'period': item['_id'],
                'protest_count': current_count,
                'avg_quality_score': round(item.get('avg_quality_score', 0), 2),
                'verified_count': item.get('verified_count', 0),
                'verification_rate': safe_divide(item.get('verified_count', 0), current_count),
                'growth_rate_percent': round(growth_rate, 1) if len(formatted_time_series) > 0 else None
            })
            previous_count = current_count
        
        # Format category trends
        category_trends_formatted = {}
        for item in category_trends_data:
            category = item['_id']['category']
            period = item['_id']['period']
            
            if category not in category_trends_formatted:
                category_trends_formatted[category] = []
            
            category_trends_formatted[category].append({
                'period': period,
                'count': item['count'],
                'avg_trending_score': round(item.get('avg_trending_score', 0), 2)
            })
        
        # Format geographic trends
        geographic_trends_formatted = {}
        for item in geographic_trends_data:
            country = item['_id']['country']
            period = item['_id']['period']
            
            if country not in geographic_trends_formatted:
                geographic_trends_formatted[country] = []
            
            geographic_trends_formatted[country].append({
                'period': period,
                'count': item['count'],
                'avg_quality': round(item.get('avg_quality', 0), 2)
            })
        
        # Calculate summary statistics
        total_protests = sum(item['protest_count'] for item in time_series_data)
        avg_protests_per_period = safe_divide(total_protests, len(time_series_data))
        
        # Find peak activity period
        peak_period = max(time_series_data, key=lambda x: x['protest_count']) if time_series_data else None
        
        return jsonify({
            'success': True,
            'message': 'Protest trends retrieved successfully',
            'data': {
                'time_series': {
                    'data': formatted_time_series,
                    'granularity': granularity,
                    'total_protests': total_protests,
                    'avg_per_period': round(avg_protests_per_period, 1),
                    'peak_period': {
                        'period': peak_period['_id'],
                        'count': peak_period['protest_count']
                    } if peak_period else None
                },
                'category_trends': category_trends_formatted,
                'geographic_trends': geographic_trends_formatted,
                'analysis_period': {
                    'selected': period,
                    'granularity': granularity,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'total_days': (end_date - start_date).days
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Protest trends error: {e}")
        error_log_model.log_error(
            service_name="analytics_service",
            error_type="protest_trends_error",
            error_message=str(e),
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve protest trends',
            'message': 'An error occurred while retrieving protest trends'
        }), 500


@bp.route('/analytics/protests/statistics', methods=['GET'])
def get_protest_statistics():
    """Get comprehensive protest statistics"""
    try:
        period = request.args.get('period', '30d')
        include_comparisons = request.args.get('include_comparisons', 'true').lower() == 'true'
        
        start_date, end_date = get_date_range(period)
        
        # Basic statistics for current period
        current_stats = {
            'total_protests': protest_model.count({
                'visibility': 'public',
                'start_date': {'$gte': start_date, '$lte': end_date}
            }),
            'active_protests': protest_model.count({
                'visibility': 'public',
                'status': {'$in': ['active', 'ongoing']},
                'start_date': {'$gte': start_date, '$lte': end_date}
            }),
            'verified_protests': protest_model.count({
                'visibility': 'public',
                'verification_status': 'verified',
                'start_date': {'$gte': start_date, '$lte': end_date}
            }),
            'featured_protests': protest_model.count({
                'visibility': 'public',
                'featured': True,
                'start_date': {'$gte': start_date, '$lte': end_date}
            })
        }
        
        # Quality score statistics
        quality_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'avg_quality': {'$avg': '$data_quality_score'},
                    'min_quality': {'$min': '$data_quality_score'},
                    'max_quality': {'$max': '$data_quality_score'},
                    'high_quality_count': {
                        '$sum': {
                            '$cond': [{'$gte': ['$data_quality_score', 0.8]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        quality_stats = aggregate_with_fallback(
            protest_model.collection, 
            quality_pipeline, 
            [{'_id': None, 'avg_quality': 0, 'min_quality': 0, 'max_quality': 0, 'high_quality_count': 0}]
        )
        
        quality_data = quality_stats[0] if quality_stats else {}
        
        # Verification status breakdown
        verification_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': '$verification_status',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        verification_breakdown = aggregate_with_fallback(
            protest_model.collection, 
            verification_pipeline, 
            []
        )
        
        # Status breakdown
        status_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        status_breakdown = aggregate_with_fallback(
            protest_model.collection, 
            status_pipeline, 
            []
        )
        
        # Data source statistics
        source_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {'$unwind': '$data_sources'},
            {
                '$group': {
                    '_id': '$data_sources',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}}
        ]
        
        source_breakdown = aggregate_with_fallback(
            protest_model.collection, 
            source_pipeline, 
            []
        )
        
        # Engagement statistics
        engagement_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_views': {'$sum': '$engagement_metrics.views'},
                    'total_shares': {'$sum': '$engagement_metrics.shares'},
                    'total_bookmarks': {'$sum': '$engagement_metrics.bookmarks'},
                    'avg_views': {'$avg': '$engagement_metrics.views'},
                    'avg_shares': {'$avg': '$engagement_metrics.shares'},
                    'avg_bookmarks': {'$avg': '$engagement_metrics.bookmarks'}
                }
            }
        ]
        
        engagement_stats = aggregate_with_fallback(
            protest_model.collection, 
            engagement_pipeline, 
            [{'_id': None, 'total_views': 0, 'total_shares': 0, 'total_bookmarks': 0, 
              'avg_views': 0, 'avg_shares': 0, 'avg_bookmarks': 0}]
        )
        
        engagement_data = engagement_stats[0] if engagement_stats else {}
        
        # Comparison with previous period (if requested)
        comparison_data = None
        if include_comparisons:
            period_length = end_date - start_date
            prev_start = start_date - period_length
            prev_end = start_date
            
            prev_stats = {
                'total_protests': protest_model.count({
                    'visibility': 'public',
                    'start_date': {'$gte': prev_start, '$lte': prev_end}
                }),
                'verified_protests': protest_model.count({
                    'visibility': 'public',
                    'verification_status': 'verified',
                    'start_date': {'$gte': prev_start, '$lte': prev_end}
                })
            }
            
            comparison_data = {
                'previous_period': {
                    'start_date': prev_start.isoformat(),
                    'end_date': prev_end.isoformat(),
                    'statistics': prev_stats
                },
                'growth_rates': {
                    'total_protests': calculate_growth_rate(
                        current_stats['total_protests'], 
                        prev_stats['total_protests']
                    ),
                    'verified_protests': calculate_growth_rate(
                        current_stats['verified_protests'], 
                        prev_stats['verified_protests']
                    )
                }
            }
        
        # Calculate derived metrics
        verification_rate = safe_divide(current_stats['verified_protests'], current_stats['total_protests'])
        activity_rate = safe_divide(current_stats['active_protests'], current_stats['total_protests'])
        feature_rate = safe_divide(current_stats['featured_protests'], current_stats['total_protests'])
        high_quality_rate = safe_divide(quality_data.get('high_quality_count', 0), current_stats['total_protests'])
        
        return jsonify({
            'success': True,
            'message': 'Protest statistics retrieved successfully',
            'data': {
                'current_period_stats': current_stats,
                'quality_metrics': {
                    'average_quality_score': round(quality_data.get('avg_quality', 0), 3),
                    'min_quality_score': round(quality_data.get('min_quality', 0), 3),
                    'max_quality_score': round(quality_data.get('max_quality', 0), 3),
                    'high_quality_count': quality_data.get('high_quality_count', 0),
                    'high_quality_rate': round(high_quality_rate, 3)
                },
                'rates_and_percentages': {
                    'verification_rate': round(verification_rate, 3),
                    'activity_rate': round(activity_rate, 3),
                    'feature_rate': round(feature_rate, 3),
                    'high_quality_rate': round(high_quality_rate, 3)
                },
                'breakdowns': {
                    'by_verification_status': {
                        item['_id']: item['count'] for item in verification_breakdown
                    },
                    'by_status': {
                        item['_id']: item['count'] for item in status_breakdown
                    },
                    'by_data_source': [
                        {'source': item['_id'], 'count': item['count']} 
                        for item in source_breakdown
                    ]
                },
                'engagement_metrics': {
                    'total_views': engagement_data.get('total_views', 0),
                    'total_shares': engagement_data.get('total_shares', 0),
                    'total_bookmarks': engagement_data.get('total_bookmarks', 0),
                    'average_views_per_protest': round(engagement_data.get('avg_views', 0), 1),
                    'average_shares_per_protest': round(engagement_data.get('avg_shares', 0), 1),
                    'average_bookmarks_per_protest': round(engagement_data.get('avg_bookmarks', 0), 1)
                },
                'comparison': comparison_data,
                'analysis_period': {
                    'selected': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Protest statistics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve protest statistics',
            'message': 'An error occurred while retrieving protest statistics'
        }), 500


# =====================================================
# GEOGRAPHIC ANALYTICS ENDPOINTS
# =====================================================

@bp.route('/analytics/geographic', methods=['GET'])
def get_geographic_analytics():
    """Get geographic analysis and mapping data"""
    try:
        period = request.args.get('period', '90d')
        granularity = request.args.get('granularity', 'country')  # country, region, city
        
        start_date, end_date = get_date_range(period)
        
        # Country-level analysis
        country_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': '$source_metadata.country',
                    'protest_count': {'$sum': 1},
                    'avg_quality_score': {'$avg': '$data_quality_score'},
                    'verified_count': {
                        '$sum': {
                            '$cond': [{'$eq': ['$verification_status', 'verified']}, 1, 0]
                        }
                    },
                    'avg_trending_score': {'$avg': '$trending_score'},
                    'active_protests': {
                        '$sum': {
                            '$cond': [{'$in': ['$status', ['active', 'ongoing']]}, 1, 0]
                        }
                    }
                }
            },
            {'$match': {'_id': {'$ne': None, '$ne': ''}}},
            {'$sort': {'protest_count': -1}},
            {'$limit': 50}
        ]
        
        country_data = aggregate_with_fallback(
            protest_model.collection, 
            country_pipeline, 
            []
        )
        
        # Region-based analysis (using location description)
        region_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date},
                    'location_description': {'$ne': None, '$ne': ''}
                }
            },
            {
                '$project': {
                    'location_description': 1,
                    'data_quality_score': 1,
                    'verification_status': 1,
                    'status': 1,
                    'trending_score': 1,
                    'location_parts': {'$split': ['$location_description', ',']}
                }
            },
            {
                '$project': {
                    'location_description': 1,
                    'data_quality_score': 1,
                    'verification_status': 1,
                    'status': 1,
                    'trending_score': 1,
                    'primary_location': {'$arrayElemAt': ['$location_parts', 0]}
                }
            },
            {
                '$group': {
                    '_id': {'$trim': {'input': '$primary_location'}},
                    'protest_count': {'$sum': 1},
                    'avg_quality_score': {'$avg': '$data_quality_score'},
                    'verified_count': {
                        '$sum': {
                            '$cond': [{'$eq': ['$verification_status', 'verified']}, 1, 0]
                        }
                    }
                }
            },
            {'$match': {'_id': {'$ne': None, '$ne': ''}}},
            {'$sort': {'protest_count': -1}},
            {'$limit': 30}
        ]
        
        region_data = aggregate_with_fallback(
            protest_model.collection, 
            region_pipeline, 
            []
        )
        
        # Geographic distribution by coordinates (for heatmap)
        coordinates_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date},
                    'location.coordinates': {'$ne': [0, 0]}
                }
            },
            {
                '$project': {
                    'coordinates': '$location.coordinates',
                    'trending_score': 1,
                    'data_quality_score': 1
                }
            },
            {'$limit': 1000}  # Limit for performance
        ]
        
        coordinates_data = aggregate_with_fallback(
            protest_model.collection, 
            coordinates_pipeline, 
            []
        )
        
        # Format country data
        formatted_countries = []
        for item in country_data:
            verification_rate = safe_divide(item['verified_count'], item['protest_count'])
            activity_rate = safe_divide(item['active_protests'], item['protest_count'])
            
            formatted_countries.append({
                'country': item['_id'],
                'protest_count': item['protest_count'],
                'avg_quality_score': round(item.get('avg_quality_score', 0), 2),
                'verified_count': item['verified_count'],
                'verification_rate': round(verification_rate, 3),
                'active_protests': item['active_protests'],
                'activity_rate': round(activity_rate, 3),
                'avg_trending_score': round(item.get('avg_trending_score', 0), 2)
            })
        
        # Format region data
        formatted_regions = []
        for item in region_data:
            verification_rate = safe_divide(item['verified_count'], item['protest_count'])
            
            formatted_regions.append({
                'region': item['_id'],
                'protest_count': item['protest_count'],
                'avg_quality_score': round(item.get('avg_quality_score', 0), 2),
                'verified_count': item['verified_count'],
                'verification_rate': round(verification_rate, 3)
            })
        
        # Format coordinates for heatmap
        heatmap_points = []
        for item in coordinates_data:
            coords = item.get('coordinates', [0, 0])
            if coords != [0, 0] and len(coords) == 2:
                heatmap_points.append({
                    'latitude': coords[1],
                    'longitude': coords[0],
                    'intensity': item.get('trending_score', 1),
                    'quality': item.get('data_quality_score', 0.5)
                })
        
        # Calculate geographic diversity
        total_countries = len(formatted_countries)
        total_regions = len(formatted_regions)
        
        # Find top protest hotspots
        top_countries = formatted_countries[:5]
        top_regions = formatted_regions[:5]
        
        return jsonify({
            'success': True,
            'message': 'Geographic analytics retrieved successfully',
            'data': {
                'country_analysis': {
                    'data': formatted_countries,
                    'total_countries': total_countries,
                    'top_countries': top_countries
                },
                'region_analysis': {
                    'data': formatted_regions,
                    'total_regions': total_regions,
                    'top_regions': top_regions
                },
                'heatmap_data': {
                    'points': heatmap_points,
                    'total_points': len(heatmap_points),
                    'note': 'Coordinates with non-zero values only'
                },
                'geographic_diversity': {
                    'countries_with_protests': total_countries,
                    'regions_with_protests': total_regions,
                    'geographic_spread_index': min(100, total_countries * 2)  # Simple index
                },
                'analysis_period': {
                    'selected': period,
                    'granularity': granularity,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Geographic analytics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve geographic analytics',
            'message': 'An error occurred while retrieving geographic analytics'
        }), 500


# =====================================================
# CATEGORY ANALYTICS ENDPOINTS
# =====================================================

@bp.route('/analytics/categories', methods=['GET'])
def get_category_analytics():
    """Get category-based analytics and insights"""
    try:
        period = request.args.get('period', '90d')
        include_trends = request.args.get('include_trends', 'true').lower() == 'true'
        
        start_date, end_date = get_date_range(period)
        
        # Category distribution and statistics
        category_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {'$unwind': '$categories'},
            {
                '$group': {
                    '_id': '$categories',
                    'protest_count': {'$sum': 1},
                    'avg_quality_score': {'$avg': '$data_quality_score'},
                    'avg_trending_score': {'$avg': '$trending_score'},
                    'verified_count': {
                        '$sum': {
                            '$cond': [{'$eq': ['$verification_status', 'verified']}, 1, 0]
                        }
                    },
                    'active_count': {
                        '$sum': {
                            '$cond': [{'$in': ['$status', ['active', 'ongoing']]}, 1, 0]
                        }
                    },
                    'total_views': {'$sum': '$engagement_metrics.views'},
                    'total_bookmarks': {'$sum': '$engagement_metrics.bookmarks'}
                }
            },
            {'$sort': {'protest_count': -1}},
            {'$limit': 20}
        ]
        
        category_data = aggregate_with_fallback(
            protest_model.collection, 
            category_pipeline, 
            []
        )
        
        # Category trends over time (if requested)
        category_trends = {}
        if include_trends:
            trends_pipeline = [
                {
                    '$match': {
                        'visibility': 'public',
                        'start_date': {'$gte': start_date, '$lte': end_date}
                    }
                },
                {'$unwind': '$categories'},
                {
                    '$group': {
                        '_id': {
                            'category': '$categories',
                            'month': {
                                '$dateToString': {
                                    'format': '%Y-%m',
                                    'date': '$start_date'
                                }
                            }
                        },
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id.month': 1}}
            ]
            
            trends_data = aggregate_with_fallback(
                protest_model.collection, 
                trends_pipeline, 
                []
            )
            
            # Format trends data
            for item in trends_data:
                category = item['_id']['category']
                month = item['_id']['month']
                
                if category not in category_trends:
                    category_trends[category] = []
                
                category_trends[category].append({
                    'month': month,
                    'count': item['count']
                })
        
        # Category co-occurrence analysis
        cooccurrence_pipeline = [
            {
                '$match': {
                    'visibility': 'public',
                    'start_date': {'$gte': start_date, '$lte': end_date},
                    'categories': {'$size': {'$gte': 2}}  # Only protests with multiple categories
                }
            },
            {
                '$project': {
                    'category_pairs': {
                        '$map': {
                            'input': {'$range': [0, {'$size': '$categories'}]},
                            'as': 'i',
                            'in': {
                                '$map': {
                                    'input': {'$range': [{'$add': ['$i', 1]}, {'$size': '$categories'}]},
                                    'as': 'j',
                                    'in': {
                                        'cat1': {'$arrayElemAt': ['$categories', '$i']},
                                        'cat2': {'$arrayElemAt': ['$categories', '$j']}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {'$unwind': '$category_pairs'},
            {'$unwind': '$category_pairs'},
            {
                '$group': {
                    '_id': {
                        'cat1': '$category_pairs.cat1',
                        'cat2': '$category_pairs.cat2'
                    },
                    'cooccurrence_count': {'$sum': 1}
                }
            },
            {'$sort': {'cooccurrence_count': -1}},
            {'$limit': 15}
        ]
        
        cooccurrence_data = aggregate_with_fallback(
            protest_model.collection, 
            cooccurrence_pipeline, 
            []
        )
        
        # Format category data
        formatted_categories = []
        total_protests = sum(item['protest_count'] for item in category_data)
        
        for item in category_data:
            category = item['_id']
            protest_count = item['protest_count']
            
            # Calculate rates and percentages
            verification_rate = safe_divide(item['verified_count'], protest_count)
            activity_rate = safe_divide(item['active_count'], protest_count)
            market_share = safe_divide(protest_count, total_protests) if total_protests > 0 else 0
            
            formatted_categories.append({
                'category': category,
                'protest_count': protest_count,
                'market_share_percent': round(market_share * 100, 2),
                'avg_quality_score': round(item.get('avg_quality_score', 0), 2),
                'avg_trending_score': round(item.get('avg_trending_score', 0), 2),
                'verified_count': item['verified_count'],
                'verification_rate': round(verification_rate, 3),
                'active_count': item['active_count'],
                'activity_rate': round(activity_rate, 3),
                'total_views': item.get('total_views', 0),
                'total_bookmarks': item.get('total_bookmarks', 0),
                'avg_views_per_protest': round(safe_divide(item.get('total_views', 0), protest_count), 1),
                'avg_bookmarks_per_protest': round(safe_divide(item.get('total_bookmarks', 0), protest_count), 1)
            })
        
        # Format co-occurrence data
        formatted_cooccurrence = []
        for item in cooccurrence_data:
            formatted_cooccurrence.append({
                'category_1': item['_id']['cat1'],
                'category_2': item['_id']['cat2'],
                'cooccurrence_count': item['cooccurrence_count'],
                'relationship_strength': 'strong' if item['cooccurrence_count'] > 5 else 'moderate' if item['cooccurrence_count'] > 2 else 'weak'
            })
        
        # Calculate category insights
        top_categories = formatted_categories[:5]
        emerging_categories = [cat for cat in formatted_categories if cat['avg_trending_score'] > 0.7]
        high_quality_categories = [cat for cat in formatted_categories if cat['avg_quality_score'] > 0.8]
        
        # Category diversity metrics
        total_categories = len(formatted_categories)
        herfindahl_index = sum((cat['market_share_percent'] / 100) ** 2 for cat in formatted_categories)
        diversity_index = round(1 - herfindahl_index, 3)  # Higher = more diverse
        
        return jsonify({
            'success': True,
            'message': 'Category analytics retrieved successfully',
            'data': {
                'category_statistics': {
                    'data': formatted_categories,
                    'total_categories': total_categories,
                    'total_protests_analyzed': total_protests
                },
                'category_trends': category_trends if include_trends else None,
                'category_relationships': {
                    'cooccurrence_analysis': formatted_cooccurrence,
                    'strong_relationships': len([item for item in formatted_cooccurrence if item['relationship_strength'] == 'strong']),
                    'total_relationships': len(formatted_cooccurrence)
                },
                'insights': {
                    'top_categories': top_categories,
                    'emerging_categories': emerging_categories[:5],
                    'high_quality_categories': high_quality_categories[:5],
                    'most_verified_category': max(formatted_categories, key=lambda x: x['verification_rate'])['category'] if formatted_categories else None,
                    'most_active_category': max(formatted_categories, key=lambda x: x['activity_rate'])['category'] if formatted_categories else None
                },
                'diversity_metrics': {
                    'total_categories': total_categories,
                    'diversity_index': diversity_index,
                    'concentration_level': 'high' if herfindahl_index > 0.5 else 'medium' if herfindahl_index > 0.25 else 'low'
                },
                'analysis_period': {
                    'selected': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'include_trends': include_trends
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Category analytics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve category analytics',
            'message': 'An error occurred while retrieving category analytics'
        }), 500


# =====================================================
# ADVANCED ANALYTICS ENDPOINTS
# =====================================================

@bp.route('/analytics/advanced/correlations', methods=['GET'])
@auth_required(allowed_roles=['researcher', 'journalist', 'admin'])
def get_advanced_correlations():
    """Get advanced correlation analysis (for researchers and journalists)"""
    try:
        period = request.args.get('period', '180d')
        correlation_type = request.args.get('type', 'quality_engagement')  # quality_engagement, category_location, temporal_patterns
        
        start_date, end_date = get_date_range(period)
        
        if correlation_type == 'quality_engagement':
            # Analyze correlation between data quality and engagement
            quality_engagement_pipeline = [
                {
                    '$match': {
                        'visibility': 'public',
                        'start_date': {'$gte': start_date, '$lte': end_date}
                    }
                },
                {
                    '$project': {
                        'data_quality_score': 1,
                        'total_engagement': {
                            '$add': [
                                '$engagement_metrics.views',
                                {'$multiply': ['$engagement_metrics.shares', 5]},
                                {'$multiply': ['$engagement_metrics.bookmarks', 10]}
                            ]
                        },
                        'verification_status': 1
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'quality_bucket': {
                                '$switch': {
                                    'branches': [
                                        {'case': {'$gte': ['$data_quality_score', 0.8]}, 'then': 'high'},
                                        {'case': {'$gte': ['$data_quality_score', 0.6]}, 'then': 'medium'},
                                        {'case': {'$gte': ['$data_quality_score', 0.3]}, 'then': 'low'}
                                    ],
                                    'default': 'very_low'
                                }
                            }
                        },
                        'avg_engagement': {'$avg': '$total_engagement'},
                        'count': {'$sum': 1},
                        'avg_quality': {'$avg': '$data_quality_score'}
                    }
                }
            ]
            
            correlation_data = aggregate_with_fallback(
                protest_model.collection, 
                quality_engagement_pipeline, 
                []
            )
            
            analysis_results = {
                'correlation_type': 'quality_engagement',
                'data': [
                    {
                        'quality_bucket': item['_id']['quality_bucket'],
                        'avg_engagement': round(item['avg_engagement'], 2),
                        'sample_size': item['count'],
                        'avg_quality_score': round(item['avg_quality'], 3)
                    }
                    for item in correlation_data
                ]
            }
        
        elif correlation_type == 'category_location':
            # Analyze category distribution by location
            category_location_pipeline = [
                {
                    '$match': {
                        'visibility': 'public',
                        'start_date': {'$gte': start_date, '$lte': end_date},
                        'source_metadata.country': {'$ne': None, '$ne': ''}
                    }
                },
                {'$unwind': '$categories'},
                {
                    '$group': {
                        '_id': {
                            'category': '$categories',
                            'country': '$source_metadata.country'
                        },
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'count': -1}},
                {'$limit': 50}
            ]
            
            correlation_data = aggregate_with_fallback(
                protest_model.collection, 
                category_location_pipeline, 
                []
            )
            
            analysis_results = {
                'correlation_type': 'category_location',
                'data': [
                    {
                        'category': item['_id']['category'],
                        'country': item['_id']['country'],
                        'frequency': item['count']
                    }
                    for item in correlation_data
                ]
            }
        
        elif correlation_type == 'temporal_patterns':
            # Analyze temporal patterns
            temporal_pipeline = [
                {
                    '$match': {
                        'visibility': 'public',
                        'start_date': {'$gte': start_date, '$lte': end_date}
                    }
                },
                {
                    '$project': {
                        'day_of_week': {'$dayOfWeek': '$start_date'},
                        'month': {'$month': '$start_date'},
                        'hour': {'$hour': '$created_at'},
                        'categories': 1,
                        'trending_score': 1
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'day_of_week': '$day_of_week',
                            'month': '$month'
                        },
                        'protest_count': {'$sum': 1},
                        'avg_trending_score': {'$avg': '$trending_score'}
                    }
                }
            ]
            
            correlation_data = aggregate_with_fallback(
                protest_model.collection, 
                temporal_pipeline, 
                []
            )
            
            analysis_results = {
                'correlation_type': 'temporal_patterns',
                'data': [
                    {
                        'day_of_week': item['_id']['day_of_week'],
                        'month': item['_id']['month'],
                        'protest_count': item['protest_count'],
                        'avg_trending_score': round(item['avg_trending_score'], 2)
                    }
                    for item in correlation_data
                ]
            }
        
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid correlation type',
                'message': 'Supported types: quality_engagement, category_location, temporal_patterns'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Advanced correlation analysis completed',
            'data': {
                'analysis_results': analysis_results,
                'analysis_period': {
                    'selected': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'methodology': {
                    'note': 'This is advanced analytics for research purposes',
                    'sample_size': len(analysis_results['data']),
                    'analysis_type': correlation_type
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Advanced correlations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve advanced correlations',
            'message': 'An error occurred while performing advanced correlation analysis'
        }), 500


@bp.route('/analytics/custom-query', methods=['POST'])
@auth_required(allowed_roles=['researcher', 'admin'])
def custom_analytics_query():
    """Execute custom analytics queries (for researchers and admins)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing data',
                'message': 'Request body is required'
            }), 400
        
        query_type = data.get('query_type')
        parameters = data.get('parameters', {})
        
        if not query_type:
            return jsonify({
                'success': False,
                'error': 'Missing query type',
                'message': 'query_type is required'
            }), 400
        
        # Predefined safe query types
        if query_type == 'engagement_by_quality':
            # Custom query for engagement analysis by quality score ranges
            min_quality = parameters.get('min_quality', 0.0)
            max_quality = parameters.get('max_quality', 1.0)
            period_days = min(365, int(parameters.get('period_days', 30)))
            
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            pipeline = [
                {
                    '$match': {
                        'visibility': 'public',
                        'data_quality_score': {'$gte': min_quality, '$lte': max_quality},
                        'start_date': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_protests': {'$sum': 1},
                        'avg_views': {'$avg': '$engagement_metrics.views'},
                        'avg_shares': {'$avg': '$engagement_metrics.shares'},
                        'avg_bookmarks': {'$avg': '$engagement_metrics.bookmarks'},
                        'avg_quality': {'$avg': '$data_quality_score'}
                    }
                }
            ]
            
            results = aggregate_with_fallback(protest_model.collection, pipeline, [])
            
        elif query_type == 'category_growth_analysis':
            # Custom query for category growth over time
            category = parameters.get('category')
            months_back = min(24, int(parameters.get('months_back', 6)))
            
            if not category:
                return jsonify({
                    'success': False,
                    'error': 'Missing category',
                    'message': 'category parameter is required for this query type'
                }), 400
            
            start_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            pipeline = [
                {
                    '$match': {
                        'visibility': 'public',
                        'categories': category,
                        'start_date': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m',
                                'date': '$start_date'
                            }
                        },
                        'protest_count': {'$sum': 1},
                        'avg_trending_score': {'$avg': '$trending_score'},
                        'verified_count': {
                            '$sum': {
                                '$cond': [{'$eq': ['$verification_status', 'verified']}, 1, 0]
                            }
                        }
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            
            results = aggregate_with_fallback(protest_model.collection, pipeline, [])
            
        elif query_type == 'geographic_clustering':
            # Custom query for geographic clustering analysis
            country = parameters.get('country')
            radius_km = min(1000, int(parameters.get('radius_km', 100)))
            
            pipeline = [
                {
                    '$match': {
                        'visibility': 'public',
                        'location.coordinates': {'$ne': [0, 0]}
                    }
                }
            ]
            
            if country:
                pipeline[0]['$match']['source_metadata.country'] = country
            
            pipeline.extend([
                {
                    '$project': {
                        'coordinates': '$location.coordinates',
                        'data_quality_score': 1,
                        'categories': 1
                    }
                },
                {'$limit': 500}  # Limit for performance
            ])
            
            results = aggregate_with_fallback(protest_model.collection, pipeline, [])
            
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid query type',
                'message': f'Query type "{query_type}" is not supported'
            }), 400
        
        # Log custom query usage
        logger.info(f"Custom analytics query executed by {request.current_user['username']}: {query_type}")
        
        return jsonify({
            'success': True,
            'message': 'Custom analytics query executed successfully',
            'data': {
                'query_type': query_type,
                'parameters': parameters,
                'results': results,
                'result_count': len(results),
                'executed_at': datetime.utcnow().isoformat(),
                'executed_by': request.current_user['username']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Custom analytics query error: {e}")
        error_log_model.log_error(
            service_name="analytics_service",
            error_type="custom_query_error",
            error_message=str(e),
            user_id=request.current_user.get('id'),
            context={'query_type': data.get('query_type') if 'data' in locals() else 'unknown'},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Custom query failed',
            'message': 'An error occurred while executing the custom analytics query'
        }), 500


# =====================================================
# ANALYTICS HEALTH CHECK
# =====================================================

@bp.route('/analytics/health', methods=['GET'])
def analytics_health_check():
    """Analytics service health check"""
    try:
        # Test database connectivity
        test_protest_count = protest_model.count({'visibility': 'public'})
        test_user_count = users_model.count()
        
        # Test aggregation functionality
        try:
            test_pipeline = [
                {'$match': {'visibility': 'public'}},
                {'$group': {'_id': None, 'count': {'$sum': 1}}},
                {'$limit': 1}
            ]
            test_aggregation = list(protest_model.collection.aggregate(test_pipeline))
            aggregation_working = len(test_aggregation) > 0
        except:
            aggregation_working = False
        
        return jsonify({
            'success': True,
            'message': 'Analytics service is healthy',
            'data': {
                'service': 'analytics_service',
                'status': 'healthy',
                'database_connected': True,
                'aggregation_pipeline_working': aggregation_working,
                'available_data': {
                    'total_protests': test_protest_count,
                    'total_users': test_user_count
                },
                'features': {
                    'personal_analytics': True,
                    'protest_trends': True,
                    'protest_statistics': True,
                    'geographic_analytics': True,
                    'category_analytics': True,
                    'advanced_correlations': True,
                    'custom_queries': True
                },
                'analytics_types': [
                    'time_series', 'geographic', 'categorical', 'correlation', 
                    'engagement', 'quality', 'verification', 'trend'
                ],
                'supported_periods': ['7d', '30d', '90d', '1y', 'ytd', 'all'],
                'access_levels': {
                    'basic_analytics': ['citizen', 'activist', 'journalist', 'researcher', 'ngo_worker'],
                    'advanced_analytics': ['researcher', 'journalist', 'admin'],
                    'custom_queries': ['researcher', 'admin']
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Analytics service unhealthy',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['bp']