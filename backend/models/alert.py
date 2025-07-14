"""
Alert model for the Global Protest Tracker
Handles user notifications and alert subscriptions
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from bson import ObjectId

from .protest import BaseModel, ValidationError


class AlertModel(BaseModel):
    """Handles user alert subscriptions."""

    def __init__(self):
        super().__init__()
        self.collection = self.db.alerts

    def create(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new alert subscription for a user.

        Args:
            alert_data: Alert info including user_id and keywords

        Returns:
            The created alert

        Raises:
            ValidationError: If something's missing or wrong
        """
        # Make sure we have the basics
        required_fields = ['user_id', 'keywords']
        for field in required_fields:
            if field not in alert_data or not alert_data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Keywords can be a string or list - we'll make it a list
        if not isinstance(alert_data['keywords'], list):
            if isinstance(alert_data['keywords'], str):
                alert_data['keywords'] = [alert_data['keywords']]
            else:
                raise ValidationError("Keywords must be a list or string")
        
        # Prepare alert document
        alert_doc = self._prepare_for_insert(alert_data.copy())
        
        # Set default values
        alert_doc.setdefault('frequency', 'immediate')  # immediate, daily, weekly
        alert_doc.setdefault('location_filter', '')
        alert_doc.setdefault('categories', [])
        alert_doc.setdefault('active', True)
        alert_doc.setdefault('last_triggered', None)
        alert_doc.setdefault('trigger_count', 0)
        
        # Validate frequency
        valid_frequencies = ['immediate', 'daily', 'weekly']
        if alert_doc['frequency'] not in valid_frequencies:
            raise ValidationError(f"Invalid frequency. Must be one of: {valid_frequencies}")
        
        # Insert document
        result = self.collection.insert_one(alert_doc)
        alert_doc['_id'] = result.inserted_id
        
        return self._serialize_object_id(alert_doc)
    
    def find_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Find alert by ID."""
        try:
            if ObjectId.is_valid(alert_id):
                doc = self.collection.find_one({'_id': ObjectId(alert_id)})
            else:
                doc = self.collection.find_one({'alert_id': alert_id})
            
            return self._serialize_object_id(doc) if doc else None
        except Exception:
            return None
    
    def find_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Find all alerts for a specific user."""
        cursor = self.collection.find({'user_id': user_id}).sort('created_at', -1)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def find_active_alerts(self) -> List[Dict[str, Any]]:
        """Find all active alerts for processing."""
        cursor = self.collection.find({'active': True})
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def update(self, alert_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing alert.
        
        Args:
            alert_id: Alert ID to update
            update_data: Fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate frequency if being updated
            if 'frequency' in update_data:
                valid_frequencies = ['immediate', 'daily', 'weekly']
                if update_data['frequency'] not in valid_frequencies:
                    raise ValidationError(f"Invalid frequency. Must be one of: {valid_frequencies}")
            
            update_data = self._prepare_for_update(update_data)
            
            if ObjectId.is_valid(alert_id):
                result = self.collection.update_one(
                    {'_id': ObjectId(alert_id)},
                    {'$set': update_data}
                )
            else:
                result = self.collection.update_one(
                    {'alert_id': alert_id},
                    {'$set': update_data}
                )
            
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete(self, alert_id: str) -> bool:
        """
        Delete an alert subscription.
        
        Args:
            alert_id: Alert ID to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            if ObjectId.is_valid(alert_id):
                result = self.collection.delete_one({'_id': ObjectId(alert_id)})
            else:
                result = self.collection.delete_one({'alert_id': alert_id})
            
            return result.deleted_count > 0
        except Exception:
            return False
    
    def deactivate(self, alert_id: str) -> bool:
        """Deactivate an alert without deleting it."""
        return self.update(alert_id, {'active': False})
    
    def activate(self, alert_id: str) -> bool:
        """Activate a deactivated alert."""
        return self.update(alert_id, {'active': True})
    
    def trigger_alert(self, alert_id: str, protest_data: Dict[str, Any]) -> bool:
        """
        Record that an alert was triggered by a protest.
        
        Args:
            alert_id: Alert ID that was triggered
            protest_data: Protest data that triggered the alert
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            update_data = {
                'last_triggered': datetime.utcnow(),
                '$inc': {'trigger_count': 1}
            }
            
            if ObjectId.is_valid(alert_id):
                result = self.collection.update_one(
                    {'_id': ObjectId(alert_id)},
                    {'$set': {'last_triggered': datetime.utcnow()}, '$inc': {'trigger_count': 1}}
                )
            else:
                result = self.collection.update_one(
                    {'alert_id': alert_id},
                    {'$set': {'last_triggered': datetime.utcnow()}, '$inc': {'trigger_count': 1}}
                )
            
            return result.modified_count > 0
        except Exception:
            return False
    
    def check_alert_match(self, alert: Dict[str, Any], protest: Dict[str, Any]) -> bool:
        """
        Check if a protest matches an alert's criteria.
        
        Args:
            alert: Alert document
            protest: Protest document
            
        Returns:
            True if protest matches alert criteria, False otherwise
        """
        # Check keywords in title, description, and categories
        keywords_match = False
        for keyword in alert.get('keywords', []):
            keyword_lower = keyword.lower()
            
            # Check title
            if keyword_lower in protest.get('title', '').lower():
                keywords_match = True
                break
            
            # Check description
            if keyword_lower in protest.get('description', '').lower():
                keywords_match = True
                break
            
            # Check categories
            for category in protest.get('categories', []):
                if keyword_lower in category.lower():
                    keywords_match = True
                    break
            
            if keywords_match:
                break
        
        if not keywords_match:
            return False
        
        # Check location filter if specified
        location_filter = alert.get('location_filter', '').strip()
        if location_filter:
            protest_location = protest.get('location', {})
            if isinstance(protest_location, str):
                protest_location_str = protest_location.lower()
            else:
                protest_location_str = f"{protest_location.get('city', '')} {protest_location.get('country', '')}".lower()
            
            if location_filter.lower() not in protest_location_str:
                return False
        
        # Check categories filter if specified
        alert_categories = alert.get('categories', [])
        if alert_categories:
            protest_categories = protest.get('categories', [])
            if not any(cat in protest_categories for cat in alert_categories):
                return False
        
        return True
    
    def find_matching_alerts(self, protest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find all active alerts that match a given protest.
        
        Args:
            protest: Protest document to match against
            
        Returns:
            List of matching alert documents
        """
        active_alerts = self.find_active_alerts()
        matching_alerts = []
        
        for alert in active_alerts:
            if self.check_alert_match(alert, protest):
                matching_alerts.append(alert)
        
        return matching_alerts
    
    def get_user_alert_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get alert statistics for a specific user."""
        user_alerts = self.find_by_user(user_id)
        
        total_alerts = len(user_alerts)
        active_alerts = len([a for a in user_alerts if a.get('active', True)])
        total_triggers = sum(a.get('trigger_count', 0) for a in user_alerts)
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'inactive_alerts': total_alerts - active_alerts,
            'total_triggers': total_triggers,
            'last_updated': datetime.utcnow().isoformat()
        }
