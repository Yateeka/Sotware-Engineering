"""
Admin Action model for the Global Protest Tracker
Keeps track of everything admins do for auditing
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from bson import ObjectId

from .protest import BaseModel, ValidationError


class AdminActionModel(BaseModel):
    """Logs everything admins do for security and auditing."""

    def __init__(self):
        super().__init__()
        self.collection = self.db.admin_actions

    def log_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record an admin action in the audit log.

        Args:
            action_data: What the admin did (who, what, when, where)

        Returns:
            The logged action record

        Raises:
            ValidationError: If required info is missing
        """
        # Make sure we have the essential info
        required_fields = ['admin_id', 'action_type', 'target_type', 'target_id']
        for field in required_fields:
            if field not in action_data or not action_data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Check if it's a valid action type
        valid_action_types = [
            'create', 'update', 'delete', 'approve', 'reject', 'ban', 'unban',
            'verify', 'unverify', 'moderate', 'restore', 'export', 'import'
        ]
        if action_data['action_type'] not in valid_action_types:
            raise ValidationError(f"Invalid action_type. Must be one of: {valid_action_types}")

        # Check if it's a valid target type
        valid_target_types = [
            'user', 'protest', 'content', 'alert', 'system', 'data'
        ]
        if action_data['target_type'] not in valid_target_types:
            raise ValidationError(f"Invalid target_type. Must be one of: {valid_target_types}")
        
        # Prepare action document
        action_doc = self._prepare_for_insert(action_data.copy())
        
        # Set default values
        action_doc.setdefault('description', '')
        action_doc.setdefault('metadata', {})
        action_doc.setdefault('ip_address', '')
        action_doc.setdefault('user_agent', '')
        action_doc.setdefault('success', True)
        action_doc.setdefault('error_message', '')
        
        # Add timestamp for action
        action_doc['action_timestamp'] = datetime.utcnow()
        
        # Insert document
        result = self.collection.insert_one(action_doc)
        action_doc['_id'] = result.inserted_id
        
        return self._serialize_object_id(action_doc)
    
    def find_by_admin(self, admin_id: str, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Find all actions by a specific admin."""
        cursor = self.collection.find({'admin_id': admin_id}).sort('action_timestamp', -1).skip(skip).limit(limit)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def find_by_target(self, target_type: str, target_id: str) -> List[Dict[str, Any]]:
        """Find all actions on a specific target."""
        cursor = self.collection.find({
            'target_type': target_type,
            'target_id': target_id
        }).sort('action_timestamp', -1)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def find_by_action_type(self, action_type: str, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Find all actions of a specific type."""
        cursor = self.collection.find({'action_type': action_type}).sort('action_timestamp', -1).skip(skip).limit(limit)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def find_recent_actions(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Find recent actions within specified hours."""
        cutoff_time = datetime.utcnow() - datetime.timedelta(hours=hours)
        cursor = self.collection.find({
            'action_timestamp': {'$gte': cutoff_time}
        }).sort('action_timestamp', -1).limit(limit)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def find_failed_actions(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Find failed administrative actions."""
        cursor = self.collection.find({'success': False}).sort('action_timestamp', -1).skip(skip).limit(limit)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def get_admin_activity_summary(self, admin_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get activity summary for an admin over specified days.
        
        Args:
            admin_id: Admin user ID
            days: Number of days to look back
            
        Returns:
            Dictionary with activity statistics
        """
        cutoff_time = datetime.utcnow() - datetime.timedelta(days=days)
        
        # Total actions
        total_actions = self.collection.count_documents({
            'admin_id': admin_id,
            'action_timestamp': {'$gte': cutoff_time}
        })
        
        # Actions by type
        type_pipeline = [
            {
                '$match': {
                    'admin_id': admin_id,
                    'action_timestamp': {'$gte': cutoff_time}
                }
            },
            {
                '$group': {
                    '_id': '$action_type',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        action_types = {doc['_id']: doc['count'] for doc in self.collection.aggregate(type_pipeline)}
        
        # Actions by target type
        target_pipeline = [
            {
                '$match': {
                    'admin_id': admin_id,
                    'action_timestamp': {'$gte': cutoff_time}
                }
            },
            {
                '$group': {
                    '_id': '$target_type',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        target_types = {doc['_id']: doc['count'] for doc in self.collection.aggregate(target_pipeline)}
        
        # Failed actions
        failed_actions = self.collection.count_documents({
            'admin_id': admin_id,
            'action_timestamp': {'$gte': cutoff_time},
            'success': False
        })
        
        return {
            'admin_id': admin_id,
            'period_days': days,
            'total_actions': total_actions,
            'failed_actions': failed_actions,
            'success_rate': ((total_actions - failed_actions) / total_actions * 100) if total_actions > 0 else 0,
            'actions_by_type': action_types,
            'actions_by_target': target_types,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def get_system_activity_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get overall system activity summary.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with system activity statistics
        """
        cutoff_time = datetime.utcnow() - datetime.timedelta(days=days)
        
        # Total actions
        total_actions = self.collection.count_documents({
            'action_timestamp': {'$gte': cutoff_time}
        })
        
        # Unique admins
        unique_admins = len(self.collection.distinct('admin_id', {
            'action_timestamp': {'$gte': cutoff_time}
        }))
        
        # Actions by type
        type_pipeline = [
            {
                '$match': {
                    'action_timestamp': {'$gte': cutoff_time}
                }
            },
            {
                '$group': {
                    '_id': '$action_type',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'count': -1}
            }
        ]
        
        action_types = {doc['_id']: doc['count'] for doc in self.collection.aggregate(type_pipeline)}
        
        # Daily activity
        daily_pipeline = [
            {
                '$match': {
                    'action_timestamp': {'$gte': cutoff_time}
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$action_timestamp'
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id': 1}
            }
        ]
        
        daily_activity = {doc['_id']: doc['count'] for doc in self.collection.aggregate(daily_pipeline)}
        
        # Failed actions
        failed_actions = self.collection.count_documents({
            'action_timestamp': {'$gte': cutoff_time},
            'success': False
        })
        
        return {
            'period_days': days,
            'total_actions': total_actions,
            'unique_admins': unique_admins,
            'failed_actions': failed_actions,
            'success_rate': ((total_actions - failed_actions) / total_actions * 100) if total_actions > 0 else 0,
            'actions_by_type': action_types,
            'daily_activity': daily_activity,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 365) -> int:
        """
        Clean up old audit logs.
        
        Args:
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of deleted documents
        """
        cutoff_time = datetime.utcnow() - datetime.timedelta(days=days_to_keep)
        result = self.collection.delete_many({
            'action_timestamp': {'$lt': cutoff_time}
        })
        return result.deleted_count
    
    def export_logs(self, start_date: datetime, end_date: datetime, admin_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Export audit logs for a date range.
        
        Args:
            start_date: Start date for export
            end_date: End date for export
            admin_id: Optional admin ID filter
            
        Returns:
            List of audit log documents
        """
        query = {
            'action_timestamp': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        
        if admin_id:
            query['admin_id'] = admin_id
        
        cursor = self.collection.find(query).sort('action_timestamp', 1)
        return [self._serialize_object_id(doc) for doc in cursor]
