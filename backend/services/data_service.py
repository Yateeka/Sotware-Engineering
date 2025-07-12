import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

class DataService:
    """
    Data service abstraction layer.
    Handles both test data (JSON) and MongoDB operations.
    """
    
    def __init__(self, testing: bool = False, test_data_path: str = None):
        """
        Initialize data service.
        
        Args:
            testing: If True, use JSON test data. If False, use MongoDB.
            test_data_path: Path to test data JSON file.
        """
        self.testing = testing
        self.test_data_path = test_data_path
        self._test_data = None
        
        if self.testing:
            self._load_test_data()
    
    def _load_test_data(self) -> None:
        """Load test data from JSON file."""
        if not self.test_data_path:
            # Default path relative to project root
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.test_data_path = os.path.join(current_dir, 'test', 'test_data.json')
        
        try:
            with open(self.test_data_path, 'r') as f:
                self._test_data = json.load(f)
        except FileNotFoundError:
            # Fallback test data if file not found
            self._test_data = {
                "protests": [],
                "users": [],
                "alerts": []
            }
    
    def get_protests(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get protests with optional filters.
        
        Args:
            filters: Dictionary of filters to apply.
                    - location: City name to filter by
                    - cause: Cause/category to filter by  
                    - start_date: Start date for date range
                    - end_date: End date for date range
        
        Returns:
            List of protest dictionaries.
        """
        if self.testing:
            return self._get_protests_from_json(filters)
        else:
            return self._get_protests_from_mongodb(filters)
    
    def _get_protests_from_json(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get protests from JSON test data with filtering."""
        protests = self._test_data.get('protests', []).copy()
        
        if not filters:
            return protests
        
        # Apply location filter
        if 'location' in filters and filters['location']:
            city_filter = filters['location'].split(',')[0].strip()
            protests = [p for p in protests if p.get('city') == city_filter]
        
        # Apply cause filter
        if 'cause' in filters and filters['cause']:
            cause = filters['cause']
            protests = [p for p in protests if cause in p.get('categories', [])]
        
        # Apply date range filters
        if 'start_date' in filters and filters['start_date']:
            start_date = filters['start_date']
            protests = [p for p in protests if p.get('start_date', '') >= start_date]
        
        if 'end_date' in filters and filters['end_date']:
            end_date = filters['end_date']
            protests = [p for p in protests if p.get('start_date', '') <= end_date]
        
        return protests
    
    def _get_protests_from_mongodb(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get protests from MongoDB (placeholder for future implementation)."""
        # TODO: Implement MongoDB queries when database is set up
        # from models.protest import Protest
        # return Protest.find_with_filters(filters)
        raise NotImplementedError("MongoDB integration not yet implemented")
    
    def get_protest_by_id(self, protest_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific protest by ID.
        
        Args:
            protest_id: The protest ID to look up.
        
        Returns:
            Protest dictionary if found, None otherwise.
        """
        if self.testing:
            return self._get_protest_by_id_from_json(protest_id)
        else:
            return self._get_protest_by_id_from_mongodb(protest_id)
    
    def _get_protest_by_id_from_json(self, protest_id: str) -> Optional[Dict[str, Any]]:
        """Get specific protest from JSON test data."""
        protests = self._test_data.get('protests', [])
        return next((p for p in protests if p.get('protest_id') == protest_id), None)
    
    def _get_protest_by_id_from_mongodb(self, protest_id: str) -> Optional[Dict[str, Any]]:
        """Get specific protest from MongoDB (placeholder)."""
        # TODO: Implement MongoDB query
        # from models.protest import Protest
        # return Protest.find_by_id(protest_id)
        raise NotImplementedError("MongoDB integration not yet implemented")
    
    def search_protests(self, keyword: str = "") -> List[Dict[str, Any]]:
        """
        Search protests by keyword.
        
        Args:
            keyword: Search term to look for in title, description, and categories.
        
        Returns:
            List of matching protest dictionaries.
        """
        if self.testing:
            return self._search_protests_from_json(keyword)
        else:
            return self._search_protests_from_mongodb(keyword)
    
    def _search_protests_from_json(self, keyword: str = "") -> List[Dict[str, Any]]:
        """Search protests in JSON test data."""
        protests = self._test_data.get('protests', [])
        
        if not keyword:
            return protests
        
        keyword_lower = keyword.lower()
        filtered_protests = []
        
        for protest in protests:
            # Search in title
            if keyword_lower in protest.get('title', '').lower():
                filtered_protests.append(protest)
                continue
            
            # Search in description
            if keyword_lower in protest.get('description', '').lower():
                filtered_protests.append(protest)
                continue
            
            # Search in categories
            categories = protest.get('categories', [])
            if any(keyword_lower in cat.lower() for cat in categories):
                filtered_protests.append(protest)
                continue
        
        return filtered_protests
    
    def _search_protests_from_mongodb(self, keyword: str = "") -> List[Dict[str, Any]]:
        """Search protests in MongoDB (placeholder)."""
        # TODO: Implement MongoDB text search
        # from models.protest import Protest
        # return Protest.search(keyword)
        raise NotImplementedError("MongoDB integration not yet implemented")
    
    def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user alert.
        
        Args:
            alert_data: Dictionary containing alert information.
                       Required: user_id, keywords
                       Optional: location_filter
        
        Returns:
            Dictionary with success message and alert_id.
        
        Raises:
            ValueError: If required fields are missing.
        """
        if self.testing:
            return self._create_alert_from_json(alert_data)
        else:
            return self._create_alert_from_mongodb(alert_data)
    
    def _create_alert_from_json(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert in JSON test data (simulated)."""
        # Validate required fields
        required_fields = ['user_id', 'keywords']
        for field in required_fields:
            if field not in alert_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Generate alert ID
        existing_alerts = self._test_data.get('alerts', [])
        alert_id = f"alert_{len(existing_alerts) + 1}"
        
        # Create new alert
        new_alert = {
            'alert_id': alert_id,
            'user_id': alert_data['user_id'],
            'keywords': alert_data['keywords'],
            'location_filter': alert_data.get('location_filter', ''),
            'created_at': datetime.now().isoformat()
        }
        
        # Add to test data (in memory only for testing)
        self._test_data['alerts'].append(new_alert)
        
        return {
            'message': 'Alert created successfully',
            'alert_id': alert_id
        }
    
    def _create_alert_from_mongodb(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert in MongoDB (placeholder)."""
        # TODO: Implement MongoDB insert
        # from models.alert import Alert
        # return Alert.create(alert_data)
        raise NotImplementedError("MongoDB integration not yet implemented")
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID (for future use)."""
        if self.testing:
            users = self._test_data.get('users', [])
            return next((u for u in users if u.get('user_id') == user_id), None)
        else:
            # TODO: Implement MongoDB query
            raise NotImplementedError("MongoDB integration not yet implemented")