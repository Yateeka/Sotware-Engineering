import os
from pathlib import Path

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database settings
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/protest_tracker'
    
    # Data source configuration
    USE_TEST_DATA = os.environ.get('USE_TEST_DATA', 'False').lower() == 'true'
    
    # API settings
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT') or '100 per hour'
    
    # File paths
    BASE_DIR = Path(__file__).parent
    TEST_DATA_PATH = BASE_DIR / 'test' / 'test_data.json'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    USE_TEST_DATA = True  # Use JSON data in development

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    USE_TEST_DATA = True  # Always use JSON data for tests
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    USE_TEST_DATA = False  # Use MongoDB in production
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# TODO: MongoDB connection string
# TODO: API keys for GDELT, NewsAPI, GeoNames
# TODO: Secret key for sessions
# TODO: Email configuration for alerts
# TODO: Data collection intervals
