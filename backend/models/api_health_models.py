from .base_model import BaseModel
from .database import DatabaseManager
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bson import ObjectId

class ApiRateLimit(BaseModel):
    """Model for tracking API rate limits"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'api_rate_limits')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.api_rate_limits
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['source_id', 'endpoint', 'limit_type']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('requests_count', 0)
        data.setdefault('reset_time', datetime.now() + timedelta(hours=1))
        data.setdefault('max_requests', 1000)
        data.setdefault('window_minutes', 60)
        
        return data
    
    def can_make_request(self, source_id: str, endpoint: str) -> bool:
        """Check if we can make a request without hitting rate limit"""
        rate_limit = self.collection.find_one({
            'source_id': source_id,
            'endpoint': endpoint
        })
        
        if not rate_limit:
            return True
        
        # Check if reset time has passed
        if datetime.now() > rate_limit['reset_time']:
            # Reset the counter
            self.collection.update_one(
                {'_id': rate_limit['_id']},
                {
                    '$set': {
                        'requests_count': 0,
                        'reset_time': datetime.now() + timedelta(minutes=rate_limit['window_minutes'])
                    }
                }
            )
            return True
        
        return rate_limit['requests_count'] < rate_limit['max_requests']
    
    def record_request(self, source_id: str, endpoint: str, success: bool = True):
        """Record an API request"""
        self.collection.update_one(
            {'source_id': source_id, 'endpoint': endpoint},
            {
                '$inc': {'requests_count': 1},
                '$set': {'last_request': datetime.now()}
            },
            upsert=True
        )

class ServiceHealth(BaseModel):
    """Model for tracking service health and uptime"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'service_health')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.service_health
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['service_name', 'status', 'check_type']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('response_time_ms', 0)
        data.setdefault('error_details', {})
        data.setdefault('metrics', {})
        
        return data
    
    def record_health_check(self, service_name: str, status: str, 
                           response_time_ms: int = 0, error_details: Dict = None,
                           metrics: Dict = None) -> ObjectId:
        """Record a health check result"""
        data = {
            'service_name': service_name,
            'status': status,  # healthy, degraded, down
            'check_type': 'automated',
            'response_time_ms': response_time_ms,
            'error_details': error_details or {},
            'metrics': metrics or {},
            'timestamp': datetime.now()
        }
        
        return self.create(data)
    
    def get_service_status(self, service_name: str) -> Dict:
        """Get latest status for a service"""
        latest = self.collection.find_one(
            {'service_name': service_name},
            sort=[('timestamp', -1)]
        )
        
        if not latest:
            return {'status': 'unknown', 'last_check': None}
        
        return {
            'status': latest['status'],
            'last_check': latest['timestamp'],
            'response_time_ms': latest.get('response_time_ms', 0),
            'error_details': latest.get('error_details', {})
        }

class CollectionMetrics(BaseModel):
    """Model for tracking data collection metrics"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'collection_metrics')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.collection_metrics
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['metric_name', 'value', 'source_id']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('metric_type', 'counter')  # counter, gauge, histogram
        data.setdefault('tags', {})
        data.setdefault('timestamp', datetime.now())
        
        return data
    
    def record_metric(self, source_id: str, metric_name: str, value: float,
                     metric_type: str = 'counter', tags: Dict = None) -> ObjectId:
        """Record a collection metric"""
        data = {
            'source_id': source_id,
            'metric_name': metric_name,
            'value': value,
            'metric_type': metric_type,
            'tags': tags or {},
            'timestamp': datetime.now()
        }
        
        return self.create(data)
    
    def get_metrics_summary(self, source_id: str = None, hours: int = 24) -> Dict:
        """Get metrics summary for the last N hours"""
        match_stage = {
            'timestamp': {'$gte': datetime.now() - timedelta(hours=hours)}
        }
        
        if source_id:
            match_stage['source_id'] = source_id
        
        pipeline = [
            {'$match': match_stage},
            {
                '$group': {
                    '_id': {
                        'source_id': '$source_id',
                        'metric_name': '$metric_name'
                    },
                    'total_value': {'$sum': '$value'},
                    'avg_value': {'$avg': '$value'},
                    'max_value': {'$max': '$value'},
                    'count': {'$sum': 1}
                }
            }
        ]
        
        results = self.aggregate(pipeline)
        
        summary = {}
        for result in results:
            source = result['_id']['source_id']
            metric = result['_id']['metric_name']
            
            if source not in summary:
                summary[source] = {}
            
            summary[source][metric] = {
                'total': result['total_value'],
                'average': result['avg_value'],
                'maximum': result['max_value'],
                'count': result['count']
            }
        
        return summary