from .base_model import BaseModel
from .database import DatabaseManager
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bson import ObjectId

class ErrorLog(BaseModel):
    """Model for comprehensive error logging"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'error_logs')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.error_logs
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate error log data"""
        required_fields = ['service_name', 'error_type', 'error_message']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('severity', 'error')  # info, warning, error, critical
        data.setdefault('resolved', False)
        data.setdefault('context', {})
        data.setdefault('user_id', None)
        data.setdefault('request_id', None)
        
        return data
    
    def log_error(self, service_name: str, error_type: str, error_message: str,
                  stack_trace: str = None, context: Dict = None, severity: str = 'error',
                  user_id: ObjectId = None, request_id: str = None) -> ObjectId:
        """Log an error with context"""
        data = {
            'service_name': service_name,
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'context': context or {},
            'severity': severity,
            'user_id': user_id,
            'request_id': request_id,
            'timestamp': datetime.now(),
            'resolved': False
        }
        
        return self.create(data)
    
    def get_recent_errors(self, service_name: str = None, severity: str = None, 
                         hours: int = 24, limit: int = 100) -> List[Dict]:
        """Get recent errors with optional filters"""
        query = {
            'timestamp': {'$gte': datetime.now() - timedelta(hours=hours)}
        }
        
        if service_name:
            query['service_name'] = service_name
        if severity:
            query['severity'] = severity
        
        return self.find_many(query, limit=limit, sort=[('timestamp', -1)])
    
    def mark_resolved(self, error_id: ObjectId, resolved_by: str = None, notes: str = None) -> bool:
        """Mark an error as resolved"""
        update_data = {
            'resolved': True,
            'resolved_at': datetime.now()
        }
        
        if resolved_by:
            update_data['resolved_by'] = resolved_by
        if notes:
            update_data['resolution_notes'] = notes
        
        return self.update_by_id(error_id, update_data)
    
    def get_error_statistics(self, hours: int = 24) -> Dict:
        """Get error statistics for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff_time}}},
            {
                '$group': {
                    '_id': {
                        'service_name': '$service_name',
                        'severity': '$severity'
                    },
                    'count': {'$sum': 1},
                    'latest_error': {'$max': '$timestamp'}
                }
            }
        ]
        
        results = self.aggregate(pipeline)
        
        stats = {}
        total_errors = 0
        
        for result in results:
            service = result['_id']['service_name']
            severity = result['_id']['severity']
            count = result['count']
            total_errors += count
            
            if service not in stats:
                stats[service] = {}
            
            stats[service][severity] = {
                'count': count,
                'latest_error': result['latest_error']
            }
        
        return {
            'total_errors': total_errors,
            'by_service': stats,
            'time_period_hours': hours
        }

class WorkerStatus(BaseModel):
    """Model for tracking background worker status"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'worker_status')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.worker_status
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate worker status data"""
        required_fields = ['worker_id', 'worker_type', 'status']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('started_at', datetime.now())
        data.setdefault('current_task', None)
        data.setdefault('tasks_completed', 0)
        data.setdefault('tasks_failed', 0)
        data.setdefault('last_heartbeat', datetime.now())
        data.setdefault('host_info', {})
        data.setdefault('process_id', None)
        
        return data
    
    def register_worker(self, worker_id: str, worker_type: str, 
                       host_info: Dict = None, process_id: int = None) -> ObjectId:
        """Register a new worker"""
        data = {
            'worker_id': worker_id,
            'worker_type': worker_type,
            'status': 'starting',
            'host_info': host_info or {},
            'process_id': process_id,
            'started_at': datetime.now(),
            'last_heartbeat': datetime.now()
        }
        
        # Use upsert to handle worker restarts
        result = self.collection.update_one(
            {'worker_id': worker_id},
            {'$set': data},
            upsert=True
        )
        
        return result.upserted_id if result.upserted_id else None
    
    def update_heartbeat(self, worker_id: str, current_task: str = None, 
                        status: str = 'running') -> bool:
        """Update worker heartbeat"""
        update_data = {
            'last_heartbeat': datetime.now(),
            'status': status
        }
        
        if current_task:
            update_data['current_task'] = current_task
        
        result = self.collection.update_one(
            {'worker_id': worker_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    def mark_task_completed(self, worker_id: str, success: bool = True) -> bool:
        """Mark a task as completed and update statistics"""
        increment_field = 'tasks_completed' if success else 'tasks_failed'
        
        result = self.collection.update_one(
            {'worker_id': worker_id},
            {
                '$inc': {increment_field: 1},
                '$set': {
                    'current_task': None,
                    'last_task_completed': datetime.now()
                }
            }
        )
        
        return result.modified_count > 0
    
    def shutdown_worker(self, worker_id: str, reason: str = 'normal_shutdown') -> bool:
        """Mark worker as shut down"""
        update_data = {
            'status': 'stopped',
            'shutdown_at': datetime.now(),
            'shutdown_reason': reason,
            'current_task': None
        }
        
        result = self.collection.update_one(
            {'worker_id': worker_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    def get_active_workers(self, worker_type: str = None) -> List[Dict]:
        """Get all active workers"""
        query = {'status': {'$in': ['starting', 'running', 'idle']}}
        
        if worker_type:
            query['worker_type'] = worker_type
        
        return self.find_many(query, sort=[('started_at', -1)])
    
    def get_stale_workers(self, minutes: int = 5) -> List[Dict]:
        """Get workers that haven't sent heartbeat recently"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        query = {
            'status': {'$in': ['running', 'idle']},
            'last_heartbeat': {'$lt': cutoff_time}
        }
        
        return self.find_many(query)
    
    def cleanup_old_workers(self, days: int = 7) -> int:
        """Clean up old worker records"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        result = self.collection.delete_many({
            'status': 'stopped',
            'shutdown_at': {'$lt': cutoff_time}
        })
        
        return result.deleted_count
    
    def get_worker_statistics(self) -> Dict:
        """Get overall worker statistics"""
        pipeline = [
            {
                '$group': {
                    '_id': '$worker_type',
                    'total_workers': {'$sum': 1},
                    'active_workers': {
                        '$sum': {
                            '$cond': [
                                {'$in': ['$status', ['starting', 'running', 'idle']]},
                                1, 0
                            ]
                        }
                    },
                    'total_tasks_completed': {'$sum': '$tasks_completed'},
                    'total_tasks_failed': {'$sum': '$tasks_failed'},
                    'avg_uptime_hours': {
                        '$avg': {
                            '$divide': [
                                {'$subtract': ['$last_heartbeat', '$started_at']},
                                3600000  # Convert milliseconds to hours
                            ]
                        }
                    }
                }
            }
        ]
        
        results = self.aggregate(pipeline)
        
        stats = {}
        for result in results:
            worker_type = result['_id']
            stats[worker_type] = {
                'total_workers': result['total_workers'],
                'active_workers': result['active_workers'],
                'total_tasks_completed': result['total_tasks_completed'],
                'total_tasks_failed': result['total_tasks_failed'],
                'avg_uptime_hours': round(result.get('avg_uptime_hours', 0), 2),
                'success_rate': (
                    result['total_tasks_completed'] / 
                    max(result['total_tasks_completed'] + result['total_tasks_failed'], 1)
                ) * 100
            }
        
        return stats

# Export the models
__all__ = ['ErrorLog', 'WorkerStatus']