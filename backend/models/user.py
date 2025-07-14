"""
User model for the Global Protest Tracker
Handles user accounts, login, and what people are allowed to do
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
import bcrypt
import re

from .protest import BaseModel, ValidationError


class UserModel(BaseModel):
    """Handles all user-related database stuff."""

    def __init__(self):
        super().__init__()
        self.collection = self.db.users
        self.user_types_collection = self.db.user_types

        # Set up the different types of users (regular, activist, admin)
        self._initialize_user_types()

    def _initialize_user_types(self):
        """Create the different user types if they don't exist yet."""
        default_types = [
            {
                'user_type_id': 'regular',
                'type_name': 'Regular User',
                'description': 'Standard user account',
                'permissions': ['view_protests', 'create_alerts'],
                'can_submit_reports': False,
                'can_create_protests': False
            },
            {
                'user_type_id': 'verified_activist',
                'type_name': 'Verified Activist',
                'description': 'Verified activist account',
                'permissions': ['view_protests', 'create_alerts', 'submit_reports', 'create_protests'],
                'can_submit_reports': True,
                'can_create_protests': True
            },
            {
                'user_type_id': 'admin',
                'type_name': 'Administrator',
                'description': 'System administrator',
                'permissions': ['view_protests', 'create_alerts', 'submit_reports', 'create_protests', 'moderate_content', 'manage_users'],
                'can_submit_reports': True,
                'can_create_protests': True
            }
        ]
        
        for user_type in default_types:
            self.user_types_collection.update_one(
                {'user_type_id': user_type['user_type_id']},
                {'$setOnInsert': user_type},
                upsert=True
            )
    
    def _validate_email(self, email: str) -> bool:
        """Check if an email address looks valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _hash_password(self, password: str) -> str:
        """Encrypt a password so we never store it in plain text."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Check if a password matches the encrypted version."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user account.

        Args:
            user_data: All the user info (username, email, password, etc.)

        Returns:
            The new user data (without the password for security)

        Raises:
            ValidationError: If something's wrong with the data
            DuplicateKeyError: If email or username is already taken
        """
        # Make sure we have the basics
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Check if the email looks valid
        if not self._validate_email(user_data['email']):
            raise ValidationError("Invalid email format")

        # Make sure email and username aren't already taken
        existing_user = self.collection.find_one({
            '$or': [
                {'email': user_data['email']},
                {'username': user_data['username']}
            ]
        })

        if existing_user:
            if existing_user['email'] == user_data['email']:
                raise DuplicateKeyError("Email already exists")
            else:
                raise DuplicateKeyError("Username already exists")
        
        # Prepare user document
        user_doc = self._prepare_for_insert(user_data.copy())
        
        # Hash password
        user_doc['password_hash'] = self._hash_password(user_data['password'])
        del user_doc['password']  # Remove plain text password
        
        # Set default values
        user_doc.setdefault('user_type_id', 'regular')
        user_doc.setdefault('verified', False)
        user_doc.setdefault('active', True)
        user_doc.setdefault('profile', {})
        user_doc.setdefault('preferences', {
            'email_notifications': True,
            'push_notifications': False,
            'privacy_level': 'public'
        })
        user_doc.setdefault('last_login', None)
        user_doc.setdefault('login_count', 0)
        
        # Insert document
        result = self.collection.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        
        # Remove sensitive data before returning
        user_doc.pop('password_hash', None)
        
        return self._serialize_object_id(user_doc)
    
    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID."""
        try:
            if ObjectId.is_valid(user_id):
                doc = self.collection.find_one({'_id': ObjectId(user_id)})
            else:
                doc = self.collection.find_one({'user_id': user_id})
            
            if doc:
                doc.pop('password_hash', None)  # Remove sensitive data
                return self._serialize_object_id(doc)
            return None
        except Exception:
            return None
    
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email."""
        doc = self.collection.find_one({'email': email})
        if doc:
            doc.pop('password_hash', None)
            return self._serialize_object_id(doc)
        return None
    
    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username."""
        doc = self.collection.find_one({'username': username})
        if doc:
            doc.pop('password_hash', None)
            return self._serialize_object_id(doc)
        return None
    
    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User document if authentication successful, None otherwise
        """
        user = self.collection.find_one({'email': email, 'active': True})
        
        if user and self._verify_password(password, user['password_hash']):
            # Update login information
            self.collection.update_one(
                {'_id': user['_id']},
                {
                    '$set': {'last_login': datetime.utcnow()},
                    '$inc': {'login_count': 1}
                }
            )
            
            # Remove sensitive data
            user.pop('password_hash', None)
            return self._serialize_object_id(user)
        
        return None
    
    def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information."""
        try:
            update_data = self._prepare_for_update({'profile': profile_data})
            
            if ObjectId.is_valid(user_id):
                result = self.collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data}
                )
            else:
                result = self.collection.update_one(
                    {'user_id': user_id},
                    {'$set': update_data}
                )
            
            return result.modified_count > 0
        except Exception:
            return False
    
    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences."""
        try:
            update_data = self._prepare_for_update({'preferences': preferences})
            
            if ObjectId.is_valid(user_id):
                result = self.collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data}
                )
            else:
                result = self.collection.update_one(
                    {'user_id': user_id},
                    {'$set': update_data}
                )
            
            return result.modified_count > 0
        except Exception:
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        try:
            # Get user with password hash
            if ObjectId.is_valid(user_id):
                user = self.collection.find_one({'_id': ObjectId(user_id)})
            else:
                user = self.collection.find_one({'user_id': user_id})
            
            if not user:
                return False
            
            # Verify old password
            if not self._verify_password(old_password, user['password_hash']):
                return False
            
            # Update with new password
            new_hash = self._hash_password(new_password)
            update_data = self._prepare_for_update({'password_hash': new_hash})
            
            result = self.collection.update_one(
                {'_id': user['_id']},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
        except Exception:
            return False
    
    def deactivate(self, user_id: str) -> bool:
        """Deactivate user account."""
        return self.update_status(user_id, False)
    
    def activate(self, user_id: str) -> bool:
        """Activate user account."""
        return self.update_status(user_id, True)
    
    def update_status(self, user_id: str, active: bool) -> bool:
        """Update user active status."""
        try:
            update_data = self._prepare_for_update({'active': active})
            
            if ObjectId.is_valid(user_id):
                result = self.collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data}
                )
            else:
                result = self.collection.update_one(
                    {'user_id': user_id},
                    {'$set': update_data}
                )
            
            return result.modified_count > 0
        except Exception:
            return False
    
    def get_user_type(self, user_type_id: str) -> Optional[Dict[str, Any]]:
        """Get user type information."""
        return self.user_types_collection.find_one({'user_type_id': user_type_id})
    
    def get_all_user_types(self) -> List[Dict[str, Any]]:
        """Get all available user types."""
        return list(self.user_types_collection.find())
