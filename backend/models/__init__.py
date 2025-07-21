# models/__init__.py
"""
Global Protest Tracker - Model Layer
====================================

This module provides all the database models for the Global Protest Tracker system.
The system uses a dual-database architecture:

📡 Data Collection Database (protest_data_collection):
   - Raw data ingestion and processing
   - Data sources and scraping jobs
   - Processing pipeline and validation
   - API health monitoring and rate limiting
   - System configuration and caching

🌐 Web Application Database (protest_web_app):
   - User management and authentication
   - Content moderation and flagging
   - Notifications and alerts
   - Analytics and export management
   - System health and feature flags

Usage:
    from models import User, Protest, DataSource
    from models.database import DatabaseManager
"""

# Core infrastructure
from .database import DatabaseManager

# Base model class
from .base_model import BaseModel

# Data Collection Models (protest_data_collection database)
from .data_collection_models import (
    DataSource,
    RawProtestData, 
    Protest,
    ScrapingJob,
    ProtestAnalytics
)

# Data Processing Models
from .data_processing_models import (
    ProcessingRule,
    ProcessingQueue,
    ProcessingResult,
    DataValidationRule,
    DataLineage
)

# API Health & Monitoring Models
from .api_health_models import (
    ApiRateLimit,
    ServiceHealth,
    CollectionMetrics
)

# Configuration Models
from .config_models import (
    ServiceConfig,
    GeocodingCache,
    CategoryMapping
)

# System Monitoring Models
from .system_monitoring_models import (
    ErrorLog,
    WorkerStatus
)

# Web Application Models (protest_web_app database)
from .web_app_models import (
    UserType,
    User,
    UserBookmark,
    UserFollow,
    UserReport,
    Post,
    ContentFlag,
    ModerationQueue,
    UserAlert,
    UserSession,
    SystemSettings,
    UserAnalytics,
    NotificationQueue,
    NotificationHistory,
    ExportRequest,
    FeatureFlag,
    SystemHealth
)

# Model categories for easy reference
DATA_COLLECTION_MODELS = [
    'DataSource', 'RawProtestData', 'Protest', 'ScrapingJob', 'ProtestAnalytics',
    'ProcessingRule', 'ProcessingQueue', 'ProcessingResult', 'DataValidationRule', 'DataLineage',
    'ApiRateLimit', 'ServiceHealth', 'CollectionMetrics',
    'ServiceConfig', 'GeocodingCache', 'CategoryMapping',
    'ErrorLog', 'WorkerStatus'
]

WEB_APP_MODELS = [
    'UserType', 'User', 'UserBookmark', 'UserFollow', 'UserReport', 'Post',
    'ContentFlag', 'ModerationQueue', 'UserAlert', 'UserSession', 'SystemSettings',
    'UserAnalytics', 'NotificationQueue', 'NotificationHistory', 'ExportRequest',
    'FeatureFlag', 'SystemHealth'
]

ALL_MODELS = DATA_COLLECTION_MODELS + WEB_APP_MODELS

# Convenience functions
def get_data_collection_models():
    """Get all data collection model classes"""
    return {name: globals()[name] for name in DATA_COLLECTION_MODELS}

def get_web_app_models():
    """Get all web application model classes"""
    return {name: globals()[name] for name in WEB_APP_MODELS}

def get_all_models():
    """Get all model classes"""
    return {name: globals()[name] for name in ALL_MODELS}

# Version info
__version__ = "2.0.0"
__author__ = "Global Protest Tracker Team"

# Export all models
__all__ = [
    # Core
    'DatabaseManager', 'BaseModel',
    
    # Data Collection Models
    'DataSource', 'RawProtestData', 'Protest', 'ScrapingJob', 'ProtestAnalytics',
    'ProcessingRule', 'ProcessingQueue', 'ProcessingResult', 'DataValidationRule', 'DataLineage',
    'ApiRateLimit', 'ServiceHealth', 'CollectionMetrics',
    'ServiceConfig', 'GeocodingCache', 'CategoryMapping',
    'ErrorLog', 'WorkerStatus',
    
    # Web App Models  
    'UserType', 'User', 'UserBookmark', 'UserFollow', 'UserReport', 'Post',
    'ContentFlag', 'ModerationQueue', 'UserAlert', 'UserSession', 'SystemSettings',
    'UserAnalytics', 'NotificationQueue', 'NotificationHistory', 'ExportRequest',
    'FeatureFlag', 'SystemHealth',
    
    # Utility functions
    'get_data_collection_models', 'get_web_app_models', 'get_all_models',
    
    # Constants
    'DATA_COLLECTION_MODELS', 'WEB_APP_MODELS', 'ALL_MODELS'
]