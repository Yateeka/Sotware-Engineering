from .base_model import BaseModel
from .database import DatabaseManager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from bson import ObjectId
import hashlib

class DataSource(BaseModel):
    """Enhanced model for data sources in data collection database"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'data_sources')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.data_sources
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate data source creation data"""
        required_fields = ['source_id', 'name', 'type', 'endpoint_url']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('active', True)
        data.setdefault('rate_limit', 1000)
        data.setdefault('api_key_required', False)
        data.setdefault('data_quality_rating', 0.5)
        data.setdefault('last_successful_fetch', None)
        data.setdefault('error_count', 0)
        data.setdefault('success_count', 0)
        
        return data
    
    def get_active_sources(self) -> List[Dict]:
        """Get all active data sources"""
        return self.find_many({"active": True})
    
    def get_by_source_id(self, source_id: str) -> Optional[Dict]:
        """Get data source by source_id"""
        return self.find_one({"source_id": source_id})
    
    def update_last_fetch(self, source_id: str, success: bool = True, error_message: str = None):
        """Update last fetch attempt and statistics"""
        update_data = {
            'last_fetch_attempt': datetime.now()
        }
        
        if success:
            update_data['last_successful_fetch'] = datetime.now()
            update_operation = {
                '$set': update_data,
                '$inc': {'success_count': 1}
            }
        else:
            update_data['last_error'] = error_message
            update_operation = {
                '$set': update_data,
                '$inc': {'error_count': 1}
            }
        
        self.collection.update_one(
            {"source_id": source_id},
            update_operation
        )
    
    def get_source_statistics(self, source_id: str) -> Dict:
        """Get statistics for a data source"""
        source = self.get_by_source_id(source_id)
        if not source:
            return {}
        
        total_attempts = source.get('success_count', 0) + source.get('error_count', 0)
        success_rate = (source.get('success_count', 0) / total_attempts) if total_attempts > 0 else 0
        
        return {
            'total_attempts': total_attempts,
            'success_count': source.get('success_count', 0),
            'error_count': source.get('error_count', 0),
            'success_rate': success_rate,
            'last_successful_fetch': source.get('last_successful_fetch'),
            'last_error': source.get('last_error')
        }

class RawProtestData(BaseModel):
    """Enhanced model for raw scraped protest data"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'raw_protest_data')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.raw_protest_data
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate raw protest data"""
        required_fields = ['source_id', 'raw_content']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Generate duplicate detection hash
        content_str = str(data['raw_content'])
        data['duplicate_hash'] = hashlib.md5(content_str.encode()).hexdigest()
        
        # Set defaults
        data.setdefault('processed_status', 'pending')
        data.setdefault('extraction_confidence', 0.5)
        data.setdefault('extraction_timestamp', datetime.now())
        data.setdefault('priority_level', 'normal')
        data.setdefault('retry_count', 0)
        
        return data
    
    def get_unprocessed(self, limit: int = 50, priority: str = None) -> List[Dict]:
        """Get unprocessed raw data with optional priority filter"""
        query = {"processed_status": "pending"}
        
        if priority:
            query['priority_level'] = priority
        
        sort_order = [("priority_level", -1), ("extraction_timestamp", 1)]
        
        return self.find_many(query, limit=limit, sort=sort_order)
    
    def mark_processed(self, doc_id: ObjectId, status: str = 'processed', result_data: Dict = None):
        """Mark raw data as processed with optional result data"""
        update_data = {
            'processed_status': status,
            'processed_at': datetime.now()
        }
        
        if result_data:
            update_data['processing_result'] = result_data
        
        self.update_by_id(doc_id, update_data)
    
    def check_duplicate(self, content_hash: str) -> bool:
        """Check if content already exists"""
        return self.collection.count_documents({"duplicate_hash": content_hash}) > 0
    
    def increment_retry_count(self, doc_id: ObjectId):
        """Increment retry count for failed processing"""
        self.update_by_id(doc_id, {}, use_set=False)
        self.collection.update_one(
            {"_id": doc_id},
            {"$inc": {"retry_count": 1}}
        )
    
    def get_processing_statistics(self) -> Dict:
        """Get processing statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$processed_status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = self.aggregate(pipeline)
        stats = {result['_id']: result['count'] for result in results}
        
        total = sum(stats.values())
        
        return {
            'total': total,
            'pending': stats.get('pending', 0),
            'processed': stats.get('processed', 0),
            'failed': stats.get('failed', 0),
            'processing_rate': (stats.get('processed', 0) / total * 100) if total > 0 else 0
        }

class Protest(BaseModel):
    """Enhanced model for processed protest data"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'protests')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.protests
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate protest data"""
        required_fields = ['title', 'location', 'start_date']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate location format for geospatial indexing
        if 'location' in data and 'coordinates' in data['location']:
            coords = data['location']['coordinates']
            if not isinstance(coords, list) or len(coords) != 2:
                raise ValueError("Invalid location coordinates format")
        
        # Set defaults
        data.setdefault('verification_status', 'unverified')
        data.setdefault('status', 'planned')
        data.setdefault('data_quality_score', 0.5)
        data.setdefault('trending_score', 0.0)
        data.setdefault('categories', [])
        data.setdefault('organizers', [])
        data.setdefault('featured', False)
        data.setdefault('visibility', 'public')
        data.setdefault('engagement_metrics', {
            'views': 0,
            'bookmarks': 0,
            'follows': 0,
            'reports_count': 0
        })
        
        return data
    
    def get_recent_protests(self, days: int = 30, limit: int = 100) -> List[Dict]:
        """Get recent protests"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.find_many(
            {"start_date": {"$gte": cutoff_date}, "visibility": "public"},
            limit=limit,
            sort=[("start_date", -1)]
        )
    
    def get_trending_protests(self, limit: int = 50) -> List[Dict]:
        """Get trending protests by trending score"""
        return self.find_many(
            {"visibility": "public", "trending_score": {"$gt": 0}},
            limit=limit,
            sort=[("trending_score", -1), ("start_date", -1)]
        )
    
    def get_featured_protests(self, limit: int = 20) -> List[Dict]:
        """Get featured protests"""
        return self.find_many(
            {"featured": True, "visibility": "public"},
            limit=limit,
            sort=[("start_date", -1)]
        )
    
    def search_by_location(self, longitude: float, latitude: float, radius_km: float = 50) -> List[Dict]:
        """Search protests by geographic location"""
        return list(self.collection.find({
            "location": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                    "$maxDistance": radius_km * 1000  # Convert km to meters
                }
            },
            "visibility": "public"
        }))
    
    def search_by_text(self, query: str, limit: int = 50) -> List[Dict]:
        """Full text search across protests"""
        return list(self.collection.find(
            {
                "$text": {"$search": query},
                "visibility": "public"
            },
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit))
    
    def get_by_categories(self, categories: List[str], limit: int = 100) -> List[Dict]:
        """Get protests by categories"""
        return self.find_many(
            {"categories": {"$in": categories}, "visibility": "public"},
            limit=limit,
            sort=[("start_date", -1)]
        )
    
    def update_engagement_metrics(self, protest_id: ObjectId, metric: str, increment: int = 1):
        """Update engagement metrics for a protest"""
        update_operation = {
            "$inc": {f"engagement_metrics.{metric}": increment}
        }
        
        self.collection.update_one({"_id": protest_id}, update_operation)
    
    def calculate_trending_score(self, protest_id: ObjectId) -> float:
        """Calculate and update trending score for a protest"""
        protest = self.find_by_id(protest_id)
        if not protest:
            return 0.0
        
        # Calculate trending score based on engagement and recency
        engagement = protest.get('engagement_metrics', {})
        views = engagement.get('views', 0)
        bookmarks = engagement.get('bookmarks', 0)
        follows = engagement.get('follows', 0)
        
        # Time decay factor (more recent = higher score)
        start_date = protest.get('start_date', datetime.now())
        days_old = (datetime.now() - start_date).days
        time_factor = max(0, 1 - (days_old / 30))  # Decay over 30 days
        
        # Engagement factor
        engagement_score = (views * 0.1) + (bookmarks * 2) + (follows * 3)
        
        # Data quality factor
        quality_score = protest.get('data_quality_score', 0.5)
        
        trending_score = (engagement_score * time_factor * quality_score) / 100
        
        # Update the protest with new trending score
        self.update_by_id(protest_id, {'trending_score': trending_score})
        
        return trending_score

class ScrapingJob(BaseModel):
    """Enhanced model for scraping job management"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'scraping_jobs')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.scraping_jobs
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate scraping job data"""
        required_fields = ['source_id', 'job_name', 'job_type']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('status', 'active')
        data.setdefault('schedule', '0 */1 * * *')  # Every hour
        data.setdefault('records_processed_last_run', 0)
        data.setdefault('success_rate', 0.0)
        data.setdefault('retry_count', 0)
        data.setdefault('max_retries', 3)
        
        return data
    
    def get_due_jobs(self) -> List[Dict]:
        """Get jobs that are due to run"""
        return self.find_many({
            "next_run": {"$lte": datetime.now()},
            "status": "active"
        })
    
    def get_jobs_by_source(self, source_id: str) -> List[Dict]:
        """Get all jobs for a specific source"""
        return self.find_many({"source_id": source_id})
    
    def update_job_status(self, job_id: ObjectId, status: str, next_run: datetime = None, 
                         records_processed: int = None, success: bool = True):
        """Update job status and statistics"""
        update_data = {
            'status': status,
            'last_run': datetime.now()
        }
        
        if next_run:
            update_data['next_run'] = next_run
        
        if records_processed is not None:
            update_data['records_processed_last_run'] = records_processed
        
        # Update success rate
        job = self.find_by_id(job_id)
        if job:
            total_runs = job.get('total_runs', 0) + 1
            successful_runs = job.get('successful_runs', 0)
            
            if success:
                successful_runs += 1
                update_data['retry_count'] = 0
            else:
                update_data['retry_count'] = job.get('retry_count', 0) + 1
            
            update_data['total_runs'] = total_runs
            update_data['successful_runs'] = successful_runs
            update_data['success_rate'] = successful_runs / total_runs
        
        self.update_by_id(job_id, update_data)
    
    def get_job_statistics(self) -> Dict:
        """Get overall job statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_success_rate": {"$avg": "$success_rate"}
                }
            }
        ]
        
        results = self.aggregate(pipeline)
        stats = {}
        
        for result in results:
            stats[result['_id']] = {
                'count': result['count'],
                'avg_success_rate': result.get('avg_success_rate', 0)
            }
        
        return stats

class ProtestAnalytics(BaseModel):
    """Model for protest analytics data"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'protest_analytics')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.protest_analytics
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate analytics data"""
        required_fields = ['protest_id', 'metric_type', 'value']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('date', datetime.now().date())
        data.setdefault('metadata', {})
        
        return data
    
    def record_metric(self, protest_id: ObjectId, metric_type: str, value: Union[int, float], 
                     metadata: Dict = None):
        """Record a metric for a protest"""
        data = {
            'protest_id': protest_id,
            'metric_type': metric_type,
            'value': value,
            'date': datetime.now().date(),
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }
        
        return self.create(data)
    
    def get_protest_metrics(self, protest_id: ObjectId, metric_type: str = None, 
                           days: int = 30) -> List[Dict]:
        """Get metrics for a specific protest"""
        query = {
            'protest_id': protest_id,
            'date': {'$gte': datetime.now().date() - timedelta(days=days)}
        }
        
        if metric_type:
            query['metric_type'] = metric_type
        
        return self.find_many(query, sort=[('date', -1)])
    
    def get_trending_analytics(self, days: int = 7) -> List[Dict]:
        """Get trending analytics across all protests"""
        pipeline = [
            {
                "$match": {
                    "date": {"$gte": datetime.now().date() - timedelta(days=days)},
                    "metric_type": {"$in": ["views", "shares", "engagement"]}
                }
            },
            {
                "$group": {
                    "_id": "$protest_id",
                    "total_engagement": {"$sum": "$value"},
                    "metrics": {"$push": {"type": "$metric_type", "value": "$value"}}
                }
            },
            {
                "$sort": {"total_engagement": -1}
            },
            {
                "$limit": 50
            }
        ]
        
        return self.aggregate(pipeline)