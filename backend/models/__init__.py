"""
Models package initialization
Database schemas and data structures for Global Protest Tracker
"""

from .protest import DatabaseConnection, BaseModel, ProtestModel
from .user import UserModel
from .alert import AlertModel
from .user_content import UserContentModel
from .admin_action import AdminActionModel

# Initialize database connection
db_connection = DatabaseConnection()

# Export model instances for easy access
protest_model = ProtestModel()
user_model = UserModel()
alert_model = AlertModel()
user_content_model = UserContentModel()
admin_action_model = AdminActionModel()

__all__ = [
    'DatabaseConnection',
    'BaseModel',
    'ProtestModel',
    'UserModel',
    'AlertModel',
    'UserContentModel',
    'AdminActionModel',
    'db_connection',
    'protest_model',
    'user_model',
    'alert_model',
    'user_content_model',
    'admin_action_model'
]
