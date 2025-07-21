import os
from pymongo import MongoClient  # MongoDB driver
from datetime import datetime
import logging

class DatabaseManager:
    """Singleton database manager for both databases"""

    _instance = None
    _client = None  # MongoDB client
    _data_collection_db = None  # Data collection DB
    _web_app_db = None  # Web app DB

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()  # Initialize connection

    def connect(self):
        """Initialize database connections"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')  # Get URI
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable not set")

            self._client = MongoClient(mongodb_uri)  # Create client
            self._data_collection_db = self._client['protest_data_collection']  # Data DB
            self._web_app_db = self._client['protest_web_app']  # App DB

            # Test connections
            self._client.admin.command('ping')  # Health check
            logging.info("Successfully connected to MongoDB")

        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    @property
    def data_collection_db(self):
        """Get data collection database"""
        return self._data_collection_db  # Return data DB

    @property
    def web_app_db(self):
        """Get web application database"""
        return self._web_app_db  # Return app DB

    def close(self):
        """Close database connections"""
        if self._client:
            self._client.close()  # Close connection