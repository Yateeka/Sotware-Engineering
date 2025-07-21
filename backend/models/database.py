import os
from pymongo import MongoClient
from datetime import datetime
import logging

class DatabaseManager:
    """Singleton database manager for both databases"""
    
    _instance = None
    _client = None
    _data_collection_db = None
    _web_app_db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self.connect()
    
    def connect(self):
        """Initialize database connections"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable not set")
            
            self._client = MongoClient(mongodb_uri)
            self._data_collection_db = self._client['protest_data_collection']
            self._web_app_db = self._client['protest_web_app']
            
            # Test connections
            self._client.admin.command('ping')
            logging.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @property
    def data_collection_db(self):
        """Get data collection database"""
        return self._data_collection_db
    
    @property
    def web_app_db(self):
        """Get web application database"""
        return self._web_app_db
    
    def close(self):
        """Close database connections"""
        if self._client:
            self._client.close()