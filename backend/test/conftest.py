import pytest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(testing=True)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def test_data():
    """Load test data from JSON file."""
    test_data_path = os.path.join(os.path.dirname(__file__), 'test_data.json')
    with open(test_data_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def sample_protest(test_data):
    """Get a sample protest for testing."""
    return test_data['protests'][0]

@pytest.fixture
def sample_user(test_data):
    """Get a sample user for testing."""
    return test_data['users'][0]