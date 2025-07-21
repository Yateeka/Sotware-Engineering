from .base_model import BaseModel
from .database import DatabaseManager
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
import json

class ServiceConfig(BaseModel):
    """Model for service configuration management"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'service_configs')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.service_configs
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['service_name', 'config_key', 'config_value']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('environment', 'production')
        data.setdefault('sensitive', False)
        data.setdefault('description', '')
        data.setdefault('config_type', 'string')  # string, int, float, bool, json
        
        return data
    
    def get_config(self, service_name: str, config_key: str, 
                   environment: str = 'production', default_value: Any = None) -> Any:
        """Get a configuration value"""
        config = self.collection.find_one({
            'service_name': service_name,
            'config_key': config_key,
            'environment': environment
        })
        
        if not config:
            return default_value
        
        value = config['config_value']
        config_type = config.get('config_type', 'string')
        
        # Convert based on type
        if config_type == 'int':
            return int(value)
        elif config_type == 'float':
            return float(value)
        elif config_type == 'bool':
            return str(value).lower() in ['true', '1', 'yes']
        elif config_type == 'json':
            return json.loads(value) if isinstance(value, str) else value
        
        return value
    
    def set_config(self, service_name: str, config_key: str, config_value: Any,
                   environment: str = 'production', config_type: str = 'string',
                   sensitive: bool = False, description: str = '') -> ObjectId:
        """Set a configuration value"""
        
        # Convert value to string for storage if needed
        if config_type == 'json':
            stored_value = json.dumps(config_value) if not isinstance(config_value, str) else config_value
        else:
            stored_value = str(config_value)
        
        data = {
            'service_name': service_name,
            'config_key': config_key,
            'config_value': stored_value,
            'environment': environment,
            'config_type': config_type,
            'sensitive': sensitive,
            'description': description
        }
        
        # Upsert the configuration
        result = self.collection.update_one(
            {
                'service_name': service_name,
                'config_key': config_key,
                'environment': environment
            },
            {'$set': data},
            upsert=True
        )
        
        return result.upserted_id if result.upserted_id else None
    
    def get_service_configs(self, service_name: str, environment: str = 'production') -> Dict:
        """Get all configurations for a service"""
        configs = self.find_many({
            'service_name': service_name,
            'environment': environment
        })
        
        result = {}
        for config in configs:
            key = config['config_key']
            value = config['config_value']
            config_type = config.get('config_type', 'string')
            
            # Convert based on type
            if config_type == 'int':
                result[key] = int(value)
            elif config_type == 'float':
                result[key] = float(value)
            elif config_type == 'bool':
                result[key] = str(value).lower() in ['true', '1', 'yes']
            elif config_type == 'json':
                result[key] = json.loads(value) if isinstance(value, str) else value
            else:
                result[key] = value
        
        return result

class GeocodingCache(BaseModel):
    """Model for caching geocoding results"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'geocoding_cache')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.geocoding_cache
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['location_string', 'coordinates']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('confidence', 0.8)
        data.setdefault('geocoder_used', 'unknown')
        data.setdefault('country', '')
        data.setdefault('admin_level_1', '')  # State/province
        data.setdefault('admin_level_2', '')  # City/county
        data.setdefault('hit_count', 0)
        
        return data
    
    def get_cached_location(self, location_string: str) -> Optional[Dict]:
        """Get cached geocoding result"""
        # Normalize location string for lookup
        normalized = location_string.lower().strip()
        
        result = self.collection.find_one({'location_string_normalized': normalized})
        
        if result:
            # Increment hit count
            self.collection.update_one(
                {'_id': result['_id']},
                {'$inc': {'hit_count': 1}}
            )
        
        return result
    
    def cache_location(self, location_string: str, coordinates: List[float],
                      confidence: float = 0.8, geocoder_used: str = 'unknown',
                      country: str = '', admin_level_1: str = '', admin_level_2: str = '') -> ObjectId:
        """Cache a geocoding result"""
        normalized = location_string.lower().strip()
        
        data = {
            'location_string': location_string,
            'location_string_normalized': normalized,
            'coordinates': coordinates,
            'confidence': confidence,
            'geocoder_used': geocoder_used,
            'country': country,
            'admin_level_1': admin_level_1,
            'admin_level_2': admin_level_2,
            'hit_count': 0
        }
        
        # Use upsert to avoid duplicates
        result = self.collection.update_one(
            {'location_string_normalized': normalized},
            {'$set': data},
            upsert=True
        )
        
        return result.upserted_id if result.upserted_id else None

class CategoryMapping(BaseModel):
    """Model for mapping keywords/phrases to protest categories"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'category_mappings')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.category_mappings
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['keywords', 'category']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('confidence_weight', 1.0)
        data.setdefault('active', True)
        data.setdefault('language', 'en')
        data.setdefault('context_required', False)
        
        return data
    
    def get_categories_for_text(self, text: str, language: str = 'en') -> List[Dict]:
        """Get potential categories for given text"""
        text_lower = text.lower()
        
        mappings = self.find_many({
            'active': True,
            'language': language
        })
        
        matches = []
        for mapping in mappings:
            keywords = mapping['keywords']
            
            # Check if any keywords match
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matches.append({
                        'category': mapping['category'],
                        'confidence': mapping['confidence_weight'],
                        'matched_keyword': keyword,
                        'context_required': mapping.get('context_required', False)
                    })
                    break  # Don't double-count the same mapping
        
        # Sort by confidence
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return matches
    
    def add_category_mapping(self, keywords: List[str], category: str,
                           confidence_weight: float = 1.0, language: str = 'en',
                           context_required: bool = False) -> ObjectId:
        """Add a new category mapping"""
        data = {
            'keywords': keywords,
            'category': category,
            'confidence_weight': confidence_weight,
            'language': language,
            'context_required': context_required,
            'active': True
        }
        
        return self.create(data)