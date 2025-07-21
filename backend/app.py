from flask import Flask
from flask_cors import CORS
import os
<<<<<<< HEAD
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
=======
>>>>>>> origin/main

from config import config
from services.data_service import DataService

# Global data service instance
data_service = None

def create_app(config_name=None, testing=False):
    """
    Application factory pattern.
    
    Args:
        config_name: Configuration to use ('development', 'testing', 'production')
        testing: Override to force testing mode
    
    Returns:
        Configured Flask application instance.
    """
    global data_service
    
    # Create Flask app
    app = Flask(__name__)
    
    # Determine configuration
    if testing:
        config_name = 'testing'
    elif config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize data service based on configuration
    use_test_data = app.config.get('USE_TEST_DATA', False)
    test_data_path = str(app.config.get('TEST_DATA_PATH')) if app.config.get('TEST_DATA_PATH') else None
    
    data_service = DataService(testing=use_test_data, test_data_path=test_data_path)
    
    # Store data service in app context for blueprints
    app.data_service = data_service
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_blueprints(app):
    """Register application blueprints."""
    # Import blueprints
    from blueprints.protests import bp as protests_bp
    from blueprints.search import bp as search_bp
    from blueprints.alerts import bp as alerts_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(protests_bp, url_prefix='/api')
    app.register_blueprint(search_bp, url_prefix='/api')
    app.register_blueprint(alerts_bp, url_prefix='/api')

def register_error_handlers(app):
    """Register application error handlers."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return {'error': 'Bad request'}, 400
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

# Basic health check endpoint
def init_basic_routes(app):
    """Initialize basic application routes."""
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {
            'status': 'healthy',
            'service': 'Global Protest Tracker API',
            'version': '1.0.0',
            'data_source': 'test_data' if app.config.get('USE_TEST_DATA') else 'mongodb'
        }

if __name__ == '__main__':
    # Create app and run in development mode
    app = create_app('development')
    init_basic_routes(app)
<<<<<<< HEAD
    app.run(debug=True, host='0.0.0.0', port=5001)
=======
    app.run(debug=True, host='0.0.0.0', port=5000)
>>>>>>> origin/main
