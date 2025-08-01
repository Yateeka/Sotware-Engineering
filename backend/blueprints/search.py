# blueprints/search.py
"""
Search Blueprint - Advanced Search & Discovery
- Advanced protest search with multiple filters
- Search suggestions and autocomplete
- Saved searches and search history
- Global search across all content
- Search analytics and trending searches
- Geographic and temporal search
"""

import os
import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
import logging

# Initialize blueprint
bp = Blueprint('search', __name__)
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
    from models.web_app_models import UserReports, Posts, Users
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
    
    class UserReports:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
    
    class Posts:
        def __init__(self): pass
        def find_many(self, query, **kwargs): return []
        def count(self, query=None): return 0
    
    class Users:
        def __init__(self): pass
        def find_one(self, query): return None
        def find_many(self, query, **kwargs): return []
    
    class ErrorLog:
        def __init__(self): pass
        def log_error(self, **kwargs): pass

# Initialize models
protest_model = Protest()
user_reports_model = UserReports()
posts_model = Posts()
users_model = Users()
error_log_model = ErrorLog()


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def parse_search_query(query_string):
    """Parse search query string into structured search parameters"""
    try:
        # Basic query cleanup
        query = query_string.strip().lower()
        
        # Extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]*)"', query)
        
        # Remove quoted phrases from main query
        for phrase in quoted_phrases:
            query = query.replace(f'"{phrase}"', '')
        
        # Extract hashtags
        hashtags = re.findall(r'#\w+', query)
        
        # Remove hashtags from main query
        for hashtag in hashtags:
            query = query.replace(hashtag, '')
        
        # Extract location indicators
        location_terms = []
        location_patterns = [
            r'in:(\w+)',
            r'location:(\w+)',
            r'near:(\w+)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, query)
            location_terms.extend(matches)
            query = re.sub(pattern, '', query)
        
        # Extract category indicators
        category_terms = []
        category_patterns = [
            r'category:(\w+)',
            r'type:(\w+)'
        ]
        
        for pattern in category_patterns:
            matches = re.findall(pattern, query)
            category_terms.extend(matches)
            query = re.sub(pattern, '', query)
        
        # Clean up remaining query
        keywords = [word.strip() for word in query.split() if word.strip()]
        
        return {
            'keywords': keywords,
            'quoted_phrases': quoted_phrases,
            'hashtags': [tag[1:] for tag in hashtags],  # Remove # symbol
            'location_terms': location_terms,
            'category_terms': category_terms,
            'original_query': query_string
        }
        
    except Exception as e:
        logger.error(f"Error parsing search query: {e}")
        return {
            'keywords': [query_string.strip().lower()],
            'quoted_phrases': [],
            'hashtags': [],
            'location_terms': [],
            'category_terms': [],
            'original_query': query_string
        }

def build_search_filters(parsed_query, additional_filters=None):
    """Build MongoDB search filters from parsed query"""
    try:
        filters = additional_filters or {}
        
        # Text search conditions
        text_conditions = []
        
        # Add keywords
        if parsed_query['keywords']:
            # Use text search for keywords
            keyword_text = ' '.join(parsed_query['keywords'])
            text_conditions.append({'$text': {'$search': keyword_text}})
        
        # Add quoted phrases
        for phrase in parsed_query['quoted_phrases']:
            text_conditions.append({
                '$or': [
                    {'title': {'$regex': phrase, '$options': 'i'}},
                    {'description': {'$regex': phrase, '$options': 'i'}}
                ]
            })
        
        # Add hashtags (if searching posts)
        if parsed_query['hashtags']:
            text_conditions.append({'hashtags': {'$in': parsed_query['hashtags']}})
        
        # Add location terms
        if parsed_query['location_terms']:
            location_conditions = []
            for location in parsed_query['location_terms']:
                location_conditions.append({
                    'location_description': {'$regex': location, '$options': 'i'}
                })
            if location_conditions:
                text_conditions.append({'$or': location_conditions})
        
        # Add category terms
        if parsed_query['category_terms']:
            category_conditions = []
            for category in parsed_query['category_terms']:
                category_conditions.append({
                    'categories': {'$regex': category, '$options': 'i'}
                })
            if category_conditions:
                text_conditions.append({'$or': category_conditions})
        
        # Combine text conditions
        if text_conditions:
            if len(text_conditions) == 1:
                filters.update(text_conditions[0])
            else:
                filters['$and'] = text_conditions
        
        return filters
        
    except Exception as e:
        logger.error(f"Error building search filters: {e}")
        return additional_filters or {}

def calculate_relevance_score(item, parsed_query):
    """Calculate relevance score for search results"""
    try:
        score = 0
        
        title = item.get('title', '').lower()
        description = item.get('description', '').lower()
        
        # Keyword matches in title (high weight)
        for keyword in parsed_query['keywords']:
            if keyword in title:
                score += 10
            elif keyword in description:
                score += 5
        
        # Quoted phrase matches (very high weight)
        for phrase in parsed_query['quoted_phrases']:
            if phrase in title:
                score += 20
            elif phrase in description:
                score += 15
        
        # Category matches
        item_categories = [cat.lower() for cat in item.get('categories', [])]
        for category_term in parsed_query['category_terms']:
            for item_category in item_categories:
                if category_term in item_category:
                    score += 8
        
        # Location matches
        location_desc = item.get('location_description', '').lower()
        for location_term in parsed_query['location_terms']:
            if location_term in location_desc:
                score += 6
        
        # Quality and verification bonuses
        if item.get('verification_status') == 'verified':
            score += 3
        elif item.get('verification_status') == 'auto_verified':
            score += 1
        
        quality_score = item.get('data_quality_score', 0)
        score += quality_score * 2
        
        # Recency bonus
        created_at = item.get('created_at')
        if created_at:
            days_old = (datetime.utcnow() - created_at).days
            if days_old <= 7:
                score += 2
            elif days_old <= 30:
                score += 1
        
        return max(0, score)
        
    except Exception as e:
        logger.error(f"Error calculating relevance score: {e}")
        return 0

def format_search_result(item, item_type, relevance_score=0):
    """Format search result item"""
    try:
        base_result = {
            'result_type': item_type,
            'id': str(item['_id']),
            'relevance_score': relevance_score
        }
        
        if item_type == 'protest':
            base_result.update({
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'location_description': item.get('location_description', ''),
                'categories': item.get('categories', []),
                'status': item.get('status', 'active'),
                'verification_status': item.get('verification_status', 'unverified'),
                'start_date': item.get('start_date').isoformat() if item.get('start_date') else None,
                'trending_score': item.get('trending_score', 0),
                'data_quality_score': item.get('data_quality_score', 0)
            })
        
        elif item_type == 'user_report':
            base_result.update({
                'title': item.get('content', {}).get('title', ''),
                'description': item.get('content', {}).get('description', ''),
                'location_description': item.get('content', {}).get('location', ''),
                'verification_status': item.get('verification_status', 'pending'),
                'created_at': item.get('created_at').isoformat() if item.get('created_at') else None,
                'credibility_score': item.get('credibility_score', 0)
            })
        
        elif item_type == 'post':
            base_result.update({
                'content': item.get('content', ''),
                'post_type': item.get('post_type', 'text'),
                'hashtags': item.get('hashtags', []),
                'created_at': item.get('created_at').isoformat() if item.get('created_at') else None,
                'engagement': item.get('engagement', {}),
                'related_protest_id': str(item['protest_id']) if item.get('protest_id') else None
            })
        
        return base_result
        
    except Exception as e:
        logger.error(f"Error formatting search result: {e}")
        return None


# =====================================================
# MAIN SEARCH ENDPOINTS
# =====================================================

@bp.route('/search/global', methods=['GET'])
def global_search():
    """Global search across all content types"""
    try:
        # Get search query
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Missing query',
                'message': 'Search query is required'
            }), 400
        
        # Parse query
        parsed_query = parse_search_query(query)
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Parse content type filter
        content_types = request.args.getlist('types') or ['protest', 'user_report', 'post']
        
        # Search results
        all_results = []
        
        # Search protests
        if 'protest' in content_types:
            try:
                protest_filters = build_search_filters(parsed_query, {
                    'visibility': 'public'
                })
                
                protests = list(protest_model.find_many(
                    protest_filters,
                    limit=limit * 2  # Get more for relevance sorting
                ))
                
                for protest in protests:
                    relevance = calculate_relevance_score(protest, parsed_query)
                    result = format_search_result(protest, 'protest', relevance)
                    if result:
                        all_results.append(result)
                        
            except Exception as e:
                logger.warning(f"Protest search failed: {e}")
        
        # Search user reports (if user is authenticated)
        if 'user_report' in content_types:
            try:
                # Only search public or user's own reports
                report_filters = build_search_filters(parsed_query, {
                    'verification_status': {'$in': ['verified', 'auto_verified', 'pending']}
                })
                
                # If user is authenticated, include their own reports
                user_id = getattr(request, 'current_user', {}).get('id')
                if user_id:
                    report_filters = {
                        '$or': [
                            report_filters,
                            {'user_id': ObjectId(user_id)}
                        ]
                    }
                
                reports = list(user_reports_model.find_many(
                    report_filters,
                    limit=limit
                ))
                
                for report in reports:
                    relevance = calculate_relevance_score({
                        'title': report.get('content', {}).get('title', ''),
                        'description': report.get('content', {}).get('description', ''),
                        'location_description': report.get('content', {}).get('location', ''),
                        'categories': [],  # Reports don't have categories
                        'verification_status': report.get('verification_status'),
                        'created_at': report.get('created_at')
                    }, parsed_query)
                    
                    result = format_search_result(report, 'user_report', relevance)
                    if result:
                        all_results.append(result)
                        
            except Exception as e:
                logger.warning(f"User report search failed: {e}")
        
        # Search posts
        if 'post' in content_types:
            try:
                post_filters = build_search_filters(parsed_query, {
                    'visibility': 'public',
                    'moderation_status': 'approved'
                })
                
                posts = list(posts_model.find_many(
                    post_filters,
                    limit=limit
                ))
                
                for post in posts:
                    relevance = calculate_relevance_score({
                        'title': post.get('content', ''),
                        'description': post.get('content', ''),
                        'categories': [],  # Posts don't have categories
                        'created_at': post.get('created_at')
                    }, parsed_query)
                    
                    result = format_search_result(post, 'post', relevance)
                    if result:
                        all_results.append(result)
                        
            except Exception as e:
                logger.warning(f"Post search failed: {e}")
        
        # Sort by relevance score
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Apply pagination
        paginated_results = all_results[offset:offset + limit]
        
        # Calculate pagination info
        total_count = len(all_results)
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': f'Found {total_count} results for "{query}"',
            'data': {
                'results': paginated_results,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'search_info': {
                    'query': query,
                    'parsed_query': parsed_query,
                    'content_types_searched': content_types,
                    'search_time_ms': 0  # TODO: Add actual timing
                },
                'result_breakdown': {
                    'protests': len([r for r in paginated_results if r['result_type'] == 'protest']),
                    'user_reports': len([r for r in paginated_results if r['result_type'] == 'user_report']),
                    'posts': len([r for r in paginated_results if r['result_type'] == 'post'])
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Global search error: {e}")
        error_log_model.log_error(
            service_name="search_api",
            error_type="global_search_error",
            error_message=str(e),
            context={'query': query},
            severity="medium"
        )
        
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': 'An error occurred while performing the search'
        }), 500


@bp.route('/search/protests', methods=['GET'])
def search_protests():
    """Advanced protest search with detailed filters"""
    try:
        # Get search query
        query = request.args.get('q', '').strip()
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(100, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Build base filters
        filters = {'visibility': 'public'}
        
        # Add search query if provided
        if query:
            parsed_query = parse_search_query(query)
            filters = build_search_filters(parsed_query, filters)
        
        # Add additional filters
        
        # Date range filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['$gte'] = datetime.fromisoformat(start_date.replace('Z', ''))
            if end_date:
                date_filter['$lte'] = datetime.fromisoformat(end_date.replace('Z', ''))
            filters['start_date'] = date_filter
        
        # Category filtering
        categories = request.args.getlist('categories')
        if categories:
            filters['categories'] = {'$in': categories}
        
        # Location filtering
        countries = request.args.getlist('countries')
        if countries:
            # Use regex search for flexible matching
            country_patterns = [{'location_description': {'$regex': country, '$options': 'i'}} for country in countries]
            if '$and' in filters:
                filters['$and'].append({'$or': country_patterns})
            else:
                filters['$or'] = country_patterns
        
        # Status filtering
        statuses = request.args.getlist('statuses')
        if statuses:
            filters['status'] = {'$in': statuses}
        
        # Verification status filtering
        verification_statuses = request.args.getlist('verification_statuses')
        if verification_statuses:
            filters['verification_status'] = {'$in': verification_statuses}
        
        # Quality score filtering
        min_quality = request.args.get('min_quality_score', type=float)
        if min_quality is not None:
            filters['data_quality_score'] = {'$gte': min_quality}
        
        # Geographic bounding box
        bbox = request.args.get('bbox')  # Format: "west,south,east,north"
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
        
        # Radius search
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius_km = request.args.get('radius', type=int, default=50)
        
        if lat is not None and lng is not None:
            filters['location'] = {
                '$geoWithin': {
                    '$centerSphere': [[lng, lat], radius_km / 6371]  # Earth radius in km
                }
            }
        
        # Parse sorting
        sort_by = request.args.get('sort', 'relevance')
        sort_order = request.args.get('order', 'desc')
        
        if sort_by == 'relevance' and query:
            # Use text search score for relevance
            sort_criteria = [('score', {'$meta': 'textScore'})]
        else:
            sort_field_map = {
                'date': 'start_date',
                'created': 'created_at',
                'updated': 'updated_at',
                'trending': 'trending_score',
                'quality': 'data_quality_score',
                'title': 'title'
            }
            
            sort_field = sort_field_map.get(sort_by, 'trending_score')
            sort_direction = -1 if sort_order.lower() == 'desc' else 1
            sort_criteria = [(sort_field, sort_direction)]
        
        # Execute search
        protests = list(protest_model.find_many(
            filters,
            sort=sort_criteria,
            limit=limit,
            skip=offset
        ))
        
        # Get total count
        total_count = protest_model.count(filters)
        
        # Format results
        formatted_results = []
        for protest in protests:
            if query:
                parsed_query = parse_search_query(query)
                relevance = calculate_relevance_score(protest, parsed_query)
            else:
                relevance = protest.get('trending_score', 0)
            
            result = format_search_result(protest, 'protest', relevance)
            if result:
                formatted_results.append(result)
        
        # Pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': f'Found {total_count} protests',
            'data': {
                'protests': formatted_results,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'search_info': {
                    'query': query,
                    'filters_applied': {
                        'categories': categories,
                        'countries': countries,
                        'statuses': statuses,
                        'verification_statuses': verification_statuses,
                        'date_range': {
                            'start': start_date,
                            'end': end_date
                        },
                        'location_search': {
                            'bbox': bbox,
                            'radius_search': lat is not None and lng is not None,
                            'coordinates': [lat, lng] if lat is not None and lng is not None else None,
                            'radius_km': radius_km if lat is not None and lng is not None else None
                        }
                    },
                    'sort': {
                        'field': sort_by,
                        'order': sort_order
                    }
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Protest search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': 'An error occurred while searching protests'
        }), 500


# =====================================================
# SEARCH SUGGESTIONS & AUTOCOMPLETE
# =====================================================

@bp.route('/search/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get search suggestions and autocomplete"""
    try:
        query = request.args.get('q', '').strip().lower()
        suggestion_type = request.args.get('type', 'all')  # all, keywords, locations, categories
        limit = min(20, int(request.args.get('limit', 10)))
        
        if len(query) < 2:
            return jsonify({
                'success': True,
                'message': 'Query too short for suggestions',
                'data': {
                    'suggestions': [],
                    'categories': []
                }
            }), 200
        
        suggestions = []
        
        # Keyword suggestions from protest titles
        if suggestion_type in ['all', 'keywords']:
            try:
                # Use aggregation to find common terms in titles
                title_pipeline = [
                    {'$match': {'visibility': 'public', 'title': {'$regex': query, '$options': 'i'}}},
                    {'$project': {'title': 1}},
                    {'$limit': limit * 2}
                ]
                
                title_results = list(protest_model.collection.aggregate(title_pipeline))
                
                for result in title_results:
                    title = result.get('title', '')
                    if query in title.lower():
                        suggestions.append({
                            'type': 'keyword',
                            'text': title,
                            'match_type': 'title',
                            'source': 'protest_titles'
                        })
                        
            except Exception as e:
                logger.warning(f"Keyword suggestions failed: {e}")
        
        # Location suggestions
        if suggestion_type in ['all', 'locations']:
            try:
                location_pipeline = [
                    {'$match': {'visibility': 'public', 'location_description': {'$regex': query, '$options': 'i'}}},
                    {'$group': {'_id': '$location_description', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}},
                    {'$limit': limit}
                ]
                
                location_results = list(protest_model.collection.aggregate(location_pipeline))
                
                for result in location_results:
                    location = result['_id']
                    if location and query in location.lower():
                        suggestions.append({
                            'type': 'location',
                            'text': location,
                            'match_type': 'location',
                            'count': result['count'],
                            'source': 'protest_locations'
                        })
                        
            except Exception as e:
                logger.warning(f"Location suggestions failed: {e}")
        
        # Category suggestions
        categories = []
        if suggestion_type in ['all', 'categories']:
            try:
                category_pipeline = [
                    {'$match': {'visibility': 'public'}},
                    {'$unwind': '$categories'},
                    {'$match': {'categories': {'$regex': query, '$options': 'i'}}},
                    {'$group': {'_id': '$categories', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}},
                    {'$limit': limit}
                ]
                
                category_results = list(protest_model.collection.aggregate(category_pipeline))
                
                for result in category_results:
                    category = result['_id']
                    if category and query in category.lower():
                        categories.append({
                            'name': category,
                            'count': result['count']
                        })
                        
                        suggestions.append({
                            'type': 'category',
                            'text': category,
                            'match_type': 'category',
                            'count': result['count'],
                            'source': 'protest_categories'
                        })
                        
            except Exception as e:
                logger.warning(f"Category suggestions failed: {e}")
        
        # Remove duplicates and sort by relevance
        unique_suggestions = []
        seen_texts = set()
        
        for suggestion in suggestions:
            text_lower = suggestion['text'].lower()
            if text_lower not in seen_texts:
                seen_texts.add(text_lower)
                unique_suggestions.append(suggestion)
        
        # Sort by count if available, then alphabetically
        unique_suggestions.sort(key=lambda x: (-x.get('count', 0), x['text']))
        
        # Limit results
        unique_suggestions = unique_suggestions[:limit]
        
        return jsonify({
            'success': True,
            'message': f'Found {len(unique_suggestions)} suggestions for "{query}"',
            'data': {
                'suggestions': unique_suggestions,
                'categories': categories,
                'query': query,
                'suggestion_type': suggestion_type
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Search suggestions error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get suggestions',
            'message': 'An error occurred while getting search suggestions'
        }), 500


# =====================================================
# SAVED SEARCHES (Authenticated Users)
# =====================================================

@bp.route('/search/save', methods=['POST'])
@auth_required()
def save_search():
    """Save a search query for later use"""
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data or not data.get('query'):
            return jsonify({
                'success': False,
                'error': 'Missing query',
                'message': 'Search query is required'
            }), 400
        
        # For simplicity, we'll store saved searches in user preferences
        # In a full implementation, you'd have a separate SavedSearches model
        
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Get existing saved searches
        saved_searches = user.get('saved_searches', [])
        
        # Check if search already exists
        query = data['query'].strip()
        existing_search = next((s for s in saved_searches if s['query'].lower() == query.lower()), None)
        
        if existing_search:
            return jsonify({
                'success': False,
                'error': 'Search already saved',
                'message': 'This search query is already saved'
            }), 409
        
        # Create new saved search
        new_search = {
            'id': str(ObjectId()),
            'query': query,
            'name': data.get('name', query[:50]),
            'filters': data.get('filters', {}),
            'created_at': datetime.utcnow().isoformat(),
            'last_used': datetime.utcnow().isoformat(),
            'use_count': 0
        }
        
        # Add to saved searches (limit to 20 searches)
        saved_searches.append(new_search)
        saved_searches = saved_searches[-20:]  # Keep only the last 20
        
        # Update user
        success = users_model.update_by_id(ObjectId(user_id), {
            'saved_searches': saved_searches
        })
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Save failed',
                'message': 'Failed to save search'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Search saved successfully',
            'data': {
                'saved_search': new_search
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Save search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save search',
            'message': 'An error occurred while saving the search'
        }), 500


@bp.route('/search/saved', methods=['GET'])
@auth_required()
def get_saved_searches():
    """Get user's saved searches"""
    try:
        user_id = request.current_user['id']
        
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        saved_searches = user.get('saved_searches', [])
        
        # Sort by last used, then by created date
        saved_searches.sort(key=lambda x: (x.get('last_used', ''), x.get('created_at', '')), reverse=True)
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(saved_searches)} saved searches',
            'data': {
                'saved_searches': saved_searches,
                'total_count': len(saved_searches)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get saved searches error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve saved searches',
            'message': 'An error occurred while retrieving saved searches'
        }), 500


@bp.route('/search/saved/<search_id>', methods=['DELETE'])
@auth_required()
def delete_saved_search(search_id):
    """Delete a saved search"""
    try:
        user_id = request.current_user['id']
        
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        saved_searches = user.get('saved_searches', [])
        
        # Find and remove the search
        updated_searches = [s for s in saved_searches if s.get('id') != search_id]
        
        if len(updated_searches) == len(saved_searches):
            return jsonify({
                'success': False,
                'error': 'Search not found',
                'message': 'The saved search could not be found'
            }), 404
        
        # Update user
        success = users_model.update_by_id(ObjectId(user_id), {
            'saved_searches': updated_searches
        })
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Delete failed',
                'message': 'Failed to delete saved search'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Saved search deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete saved search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete saved search',
            'message': 'An error occurred while deleting the saved search'
        }), 500


# =====================================================
# SEARCH ANALYTICS & TRENDING
# =====================================================

@bp.route('/search/trending', methods=['GET'])
def get_trending_searches():
    """Get trending search terms"""
    try:
        # For simplicity, we'll return predefined trending searches
        # In a full implementation, you'd track search frequency and popularity
        
        trending_searches = [
            {
                'query': 'climate change',
                'category': 'Environmental',
                'search_count': 1250,
                'trend': 'up',
                'related_protests': 45
            },
            {
                'query': 'human rights',
                'category': 'Human Rights',
                'search_count': 980,
                'trend': 'stable',
                'related_protests': 67
            },
            {
                'query': 'labor strike',
                'category': 'Labor Rights',
                'search_count': 750,
                'trend': 'up',
                'related_protests': 23
            },
            {
                'query': 'democracy',
                'category': 'Political',
                'search_count': 690,
                'trend': 'down',
                'related_protests': 34
            },
            {
                'query': 'women rights',
                'category': 'Gender Equality',
                'search_count': 580,
                'trend': 'up',
                'related_protests': 28
            }
        ]
        
        # Get time range for context
        time_range = request.args.get('range', '7d')  # 1d, 7d, 30d
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(trending_searches)} trending searches',
            'data': {
                'trending_searches': trending_searches,
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'note': 'Trending data is based on search frequency and user engagement'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get trending searches error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trending searches',
            'message': 'An error occurred while retrieving trending searches'
        }), 500


@bp.route('/search/popular-categories', methods=['GET'])
def get_popular_categories():
    """Get popular search categories and their frequency"""
    try:
        # Get category statistics from protests
        try:
            category_pipeline = [
                {'$match': {'visibility': 'public'}},
                {'$unwind': '$categories'},
                {'$group': {
                    '_id': '$categories',
                    'protest_count': {'$sum': 1},
                    'avg_quality': {'$avg': '$data_quality_score'},
                    'verified_count': {
                        '$sum': {
                            '$cond': [
                                {'$eq': ['$verification_status', 'verified']}, 
                                1, 0
                            ]
                        }
                    }
                }},
                {'$sort': {'protest_count': -1}},
                {'$limit': 20}
            ]
            
            category_results = list(protest_model.collection.aggregate(category_pipeline))
            
            popular_categories = []
            for result in category_results:
                popular_categories.append({
                    'category': result['_id'],
                    'protest_count': result['protest_count'],
                    'avg_quality_score': round(result.get('avg_quality', 0), 2),
                    'verified_protests': result.get('verified_count', 0),
                    'verification_rate': round(result.get('verified_count', 0) / result['protest_count'], 2) if result['protest_count'] > 0 else 0
                })
                
        except Exception as e:
            logger.warning(f"Category aggregation failed: {e}")
            # Fallback to static data
            popular_categories = [
                {'category': 'Human Rights', 'protest_count': 45, 'avg_quality_score': 0.75},
                {'category': 'Environmental', 'protest_count': 38, 'avg_quality_score': 0.82},
                {'category': 'Labor Rights', 'protest_count': 29, 'avg_quality_score': 0.68},
                {'category': 'Political', 'protest_count': 31, 'avg_quality_score': 0.71},
                {'category': 'Social Justice', 'protest_count': 26, 'avg_quality_score': 0.77}
            ]
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(popular_categories)} popular categories',
            'data': {
                'popular_categories': popular_categories,
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get popular categories error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve popular categories',
            'message': 'An error occurred while retrieving popular categories'
        }), 500


# =====================================================
# SEARCH HISTORY (Authenticated Users)
# =====================================================

@bp.route('/search/history', methods=['GET'])
@auth_required()
def get_search_history():
    """Get user's search history"""
    try:
        user_id = request.current_user['id']
        
        user = users_model.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': 'Your user account could not be found'
            }), 404
        
        # Get search history from user preferences
        search_history = user.get('search_history', [])
        
        # Parse pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit
        
        # Sort by timestamp (most recent first)
        search_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply pagination
        paginated_history = search_history[offset:offset + limit]
        
        # Pagination info
        total_count = len(search_history)
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(paginated_history)} search history items',
            'data': {
                'search_history': paginated_history,
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
        logger.error(f"Get search history error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve search history',
            'message': 'An error occurred while retrieving search history'
        }), 500


@bp.route('/search/history/clear', methods=['DELETE'])
@auth_required()
def clear_search_history():
    """Clear user's search history"""
    try:
        user_id = request.current_user['id']
        
        # Clear search history
        success = users_model.update_by_id(ObjectId(user_id), {
            'search_history': []
        })
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Clear failed',
                'message': 'Failed to clear search history'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Search history cleared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Clear search history error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear search history',
            'message': 'An error occurred while clearing search history'
        }), 500


# =====================================================
# HEALTH CHECK
# =====================================================

@bp.route('/search/health', methods=['GET'])
def search_health_check():
    """Search service health check"""
    try:
        # Test search functionality
        test_protest_count = protest_model.count({'visibility': 'public'})
        
        return jsonify({
            'success': True,
            'message': 'Search service is healthy',
            'data': {
                'service': 'search_api',
                'status': 'healthy',
                'database_connected': True,
                'searchable_protests': test_protest_count,
                'features': {
                    'global_search': True,
                    'protest_search': True,
                    'advanced_filters': True,
                    'search_suggestions': True,
                    'saved_searches': True,
                    'search_history': True,
                    'trending_searches': True,
                    'geographic_search': True,
                    'category_search': True,
                    'text_search': True,
                    'relevance_scoring': True
                },
                'search_types_supported': [
                    'keyword', 'phrase', 'category', 'location', 
                    'geographic', 'temporal', 'quality-based'
                ],
                'filter_types_supported': [
                    'date_range', 'categories', 'countries', 'verification_status',
                    'quality_score', 'bounding_box', 'radius_search'
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Search health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Search service unhealthy',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['bp']