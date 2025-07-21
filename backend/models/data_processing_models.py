from .base_model import BaseModel
from .database import DatabaseManager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from bson import ObjectId
import json

class ProcessingRule(BaseModel):
    """Model for data extraction and processing rules"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'processing_rules')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.processing_rules
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['rule_name', 'source_type', 'extraction_patterns']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('active', True)
        data.setdefault('priority', 5)
        data.setdefault('confidence_threshold', 0.6)
        data.setdefault('validation_rules', {})
        
        return data

class ProcessingQueue(BaseModel):
    """Model for managing data processing queue"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'processing_queue')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.processing_queue
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['raw_data_id', 'processing_type', 'priority']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('status', 'pending')
        data.setdefault('retry_count', 0)
        data.setdefault('max_retries', 3)
        data.setdefault('assigned_worker', None)
        
        return data

class ProcessingResult(BaseModel):
    """Model for storing processing results and extracted data"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'processing_results')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.processing_results
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['raw_data_id', 'extracted_data', 'confidence_score']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('validation_status', 'pending')
        data.setdefault('needs_review', False)
        data.setdefault('processing_metadata', {})
        
        return data

class DataValidationRule(BaseModel):
    """Model for data validation rules"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'validation_rules')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.validation_rules
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['rule_name', 'field_name', 'validation_type']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('active', True)
        data.setdefault('severity', 'warning')  # warning, error, critical
        data.setdefault('auto_fix', False)
        
        return data

class DataLineage(BaseModel):
    """Model for tracking data lineage and transformations"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'data_lineage')
    
    @property
    def collection(self):
        return self.db_manager.data_collection_db.data_lineage
    
    def validate_create_data(self, data: Dict) -> Dict:
        required_fields = ['source_id', 'raw_data_id']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        data.setdefault('transformations', [])
        data.setdefault('final_protest_id', None)
        data.setdefault('processing_chain', [])
        
        return data