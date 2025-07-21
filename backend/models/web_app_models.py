# models/web_app_models.py
from .base_model import BaseModel
from .database import DatabaseManager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from bson import ObjectId
import bcrypt
import secrets

class UserType(BaseModel):
    """Enhanced model for user types/roles"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'user_types')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.user_types
    
    def get_by_type_id(self, type_id: str) -> Optional[Dict]:
        """Get user type by type_id"""
        return self.collection.find_one({"user_type_id": type_id})
    
    def get_all_types(self) -> List[Dict]:
        """Get all user types ordered by hierarchy"""
        return self.find_many(sort=[("hierarchy_level", 1)])
    
    def check_permission(self, user_type_id: str, permission: str) -> bool:
        """Check if user type has specific permission"""
        user_type = self.get_by_type_id(user_type_id)
        if not user_type:
            return False
        
        permissions = user_type.get('permissions', [])
        return 'all' in permissions or permission in permissions

class User(BaseModel):
    """Enhanced model for users"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'users')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.users
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate user creation data"""
        required_fields = ['username', 'email', 'password_hash', 'user_type_id']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check for existing username/email
        if self.collection.count_documents({"username": data['username']}) > 0:
            raise ValueError("Username already exists")
        
        if self.collection.count_documents({"email": data['email']}) > 0:
            raise ValueError("Email already exists")
        
        # Set enhanced defaults
        data.setdefault('status', 'active')
        data.setdefault('verified', False)
        data.setdefault('email_verified', False)
        data.setdefault('failed_login_attempts', 0)
        data.setdefault('account_locked_until', None)
        data.setdefault('two_factor_enabled', False)
        data.setdefault('phone_number', '')
        data.setdefault('profile', {})
        data.setdefault('privacy_settings', {
            'profile_public': True,
            'show_activity': True,
            'allow_messages': True
        })
        data.setdefault('notification_settings', {
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True,
            'alert_frequency': 'immediate'
        })
        data.setdefault('statistics', {
            'login_count': 0,
            'reports_submitted': 0,
            'reports_verified': 0,
            'posts_created': 0,
            'last_active': None
        })
        
        return data
    
    def create_user(self, username: str, email: str, password: str, user_type_id: str = 'citizen') -> ObjectId:
        """Create a new user with hashed password"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash.decode('utf-8'),
            'user_type_id': user_type_id
        }
        
        return self.create(user_data)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Enhanced user authentication with security features"""
        user = self.collection.find_one({"username": username, "status": "active"})
        
        if not user:
            return None
        
        # Check if account is locked
        if user.get('account_locked_until') and user['account_locked_until'] > datetime.now():
            raise ValueError("Account is temporarily locked")
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Reset failed attempts and update login stats
            self.update_by_id(user['_id'], {
                'last_login': datetime.now(),
                'failed_login_attempts': 0,
                'account_locked_until': None,
                'statistics.last_active': datetime.now()
            }, use_set=False)
            
            # Increment login count
            self.collection.update_one(
                {"_id": user['_id']},
                {"$inc": {"statistics.login_count": 1}}
            )
            
            return user
        else:
            # Increment failed attempts
            failed_attempts = user.get('failed_login_attempts', 0) + 1
            update_data = {'failed_login_attempts': failed_attempts}
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                update_data['account_locked_until'] = datetime.now() + timedelta(minutes=30)
            
            self.update_by_id(user['_id'], update_data)
            return None
    
    def get_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        return self.collection.find_one({"username": username})
    
    def get_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return self.collection.find_one({"email": email})
    
    def update_verification_status(self, user_id: ObjectId, verified: bool = True):
        """Update user verification status"""
        update_data = {'verified': verified}
        if verified:
            update_data['verification_date'] = datetime.now()
        
        self.update_by_id(user_id, update_data)
    
    def update_email_verification(self, user_id: ObjectId, verified: bool = True):
        """Update email verification status"""
        update_data = {'email_verified': verified}
        if verified:
            update_data['email_verified_at'] = datetime.now()
        
        self.update_by_id(user_id, update_data)
    
    def get_users_by_type(self, user_type_id: str, limit: int = 100) -> List[Dict]:
        """Get users by type"""
        return self.find_many(
            {"user_type_id": user_type_id, "status": "active"},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    def search_users(self, query: str, limit: int = 50) -> List[Dict]:
        """Search users by username or email"""
        search_query = {
            "$or": [
                {"username": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
                {"profile.first_name": {"$regex": query, "$options": "i"}},
                {"profile.last_name": {"$regex": query, "$options": "i"}}
            ],
            "status": "active"
        }
        
        return self.find_many(search_query, limit=limit)

class UserBookmark(BaseModel):
    """Model for user bookmarks"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'user_bookmarks')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.user_bookmarks
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate bookmark data"""
        required_fields = ['user_id', 'protest_id']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check for existing bookmark
        existing = self.collection.find_one({
            "user_id": data['user_id'],
            "protest_id": data['protest_id']
        })
        
        if existing:
            raise ValueError("Bookmark already exists")
        
        return data
    
    def add_bookmark(self, user_id: ObjectId, protest_id: ObjectId) -> ObjectId:
        """Add a bookmark for a user"""
        data = {
            'user_id': user_id,
            'protest_id': protest_id
        }
        
        return self.create(data)
    
    def remove_bookmark(self, user_id: ObjectId, protest_id: ObjectId) -> bool:
        """Remove a bookmark"""
        result = self.collection.delete_one({
            "user_id": user_id,
            "protest_id": protest_id
        })
        
        return result.deleted_count > 0
    
    def get_user_bookmarks(self, user_id: ObjectId, limit: int = 50) -> List[Dict]:
        """Get all bookmarks for a user"""
        return self.find_many(
            {"user_id": user_id},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    def is_bookmarked(self, user_id: ObjectId, protest_id: ObjectId) -> bool:
        """Check if user has bookmarked a protest"""
        return self.collection.count_documents({
            "user_id": user_id,
            "protest_id": protest_id
        }) > 0

class UserFollow(BaseModel):
    """Model for user follows"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'user_follows')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.user_follows
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate follow data"""
        required_fields = ['user_id', 'protest_id']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('active', True)
        data.setdefault('notification_enabled', True)
        
        return data
    
    def follow_protest(self, user_id: ObjectId, protest_id: ObjectId) -> ObjectId:
        """Follow a protest"""
        # Check if already following
        existing = self.collection.find_one({
            "user_id": user_id,
            "protest_id": protest_id
        })
        
        if existing:
            # Reactivate if inactive
            self.update_by_id(existing['_id'], {'active': True})
            return existing['_id']
        
        data = {
            'user_id': user_id,
            'protest_id': protest_id,
            'active': True,
            'notification_enabled': True
        }
        
        return self.create(data)
    
    def unfollow_protest(self, user_id: ObjectId, protest_id: ObjectId) -> bool:
        """Unfollow a protest"""
        result = self.collection.update_one(
            {"user_id": user_id, "protest_id": protest_id},
            {"$set": {"active": False}}
        )
        
        return result.modified_count > 0
    
    def get_user_follows(self, user_id: ObjectId, active_only: bool = True) -> List[Dict]:
        """Get protests user is following"""
        query = {"user_id": user_id}
        if active_only:
            query["active"] = True
        
        return self.find_many(query, sort=[("created_at", -1)])

class UserReport(BaseModel):
    """Enhanced model for user-submitted protest reports"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'user_reports')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.user_reports
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate user report data"""
        required_fields = ['user_id', 'content']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set enhanced defaults
        data.setdefault('verification_status', 'pending')
        data.setdefault('credibility_score', 0.5)
        data.setdefault('priority_level', 'normal')
        data.setdefault('auto_moderation_score', 0.5)
        data.setdefault('escalated', False)
        data.setdefault('tags', [])
        data.setdefault('review_deadline', datetime.now() + timedelta(days=7))
        
        return data
    
    def get_pending_reports(self, limit: int = 50, priority: str = None) -> List[Dict]:
        """Get reports pending verification with optional priority filter"""
        query = {"verification_status": "pending"}
        
        if priority:
            query['priority_level'] = priority
        
        sort_order = [("priority_level", -1), ("created_at", 1)]
        
        return self.find_many(query, limit=limit, sort=sort_order)
    
    def get_reports_by_user(self, user_id: ObjectId, limit: int = 20) -> List[Dict]:
        """Get reports submitted by a specific user"""
        return self.find_many(
            {"user_id": user_id},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    def verify_report(self, report_id: ObjectId, verified: bool, moderator_id: ObjectId, notes: str = ""):
        """Verify/reject a user report"""
        status = "verified" if verified else "rejected"
        
        self.update_by_id(report_id, {
            'verification_status': status,
            'verified_by': moderator_id,
            'verification_date': datetime.now(),
            'verification_notes': notes
        })
        
        # Update user statistics
        report = self.find_by_id(report_id)
        if report and verified:
            user_model = User()
            user_model.collection.update_one(
                {"_id": report['user_id']},
                {"$inc": {"statistics.reports_verified": 1}}
            )
    
    def escalate_report(self, report_id: ObjectId, escalated_by: ObjectId, reason: str = ""):
        """Escalate a report for higher-level review"""
        self.update_by_id(report_id, {
            'escalated': True,
            'escalated_by': escalated_by,
            'escalated_at': datetime.now(),
            'escalation_reason': reason,
            'priority_level': 'high'
        })

class Post(BaseModel):
    """Enhanced model for user posts"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'posts')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.posts
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate post data"""
        required_fields = ['user_id', 'content']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('post_type', 'update')
        data.setdefault('visibility', 'public')
        data.setdefault('moderation_status', 'approved')
        data.setdefault('engagement', {'likes': 0, 'shares': 0, 'comments': 0})
        data.setdefault('hashtags', [])
        data.setdefault('mentions', [])
        
        return data
    
    def get_recent_posts(self, limit: int = 50, visibility: str = 'public') -> List[Dict]:
        """Get recent public posts"""
        return self.find_many(
            {"visibility": visibility, "moderation_status": "approved"},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    def get_posts_by_protest(self, protest_id: ObjectId, limit: int = 20) -> List[Dict]:
        """Get posts related to a specific protest"""
        return self.find_many(
            {"protest_id": protest_id, "moderation_status": "approved"},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    def get_posts_by_user(self, user_id: ObjectId, limit: int = 20) -> List[Dict]:
        """Get posts by a specific user"""
        return self.find_many(
            {"user_id": user_id, "moderation_status": "approved"},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    def update_engagement(self, post_id: ObjectId, action: str, increment: int = 1):
        """Update post engagement metrics"""
        if action not in ['likes', 'shares', 'comments']:
            raise ValueError("Invalid engagement action")
        
        self.collection.update_one(
            {"_id": post_id},
            {"$inc": {f"engagement.{action}": increment}}
        )

class ContentFlag(BaseModel):
    """Model for content flagging system"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'content_flags')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.content_flags
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate content flag data"""
        required_fields = ['content_type', 'content_id', 'reported_by', 'flag_type']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('status', 'pending')
        data.setdefault('description', '')
        data.setdefault('severity', 'medium')
        
        return data
    
    def flag_content(self, content_type: str, content_id: ObjectId, reported_by: ObjectId, 
                    flag_type: str, description: str = "", severity: str = "medium") -> ObjectId:
        """Flag content for review"""
        data = {
            'content_type': content_type,
            'content_id': content_id,
            'reported_by': reported_by,
            'flag_type': flag_type,
            'description': description,
            'severity': severity
        }
        
        return self.create(data)
    
    def get_pending_flags(self, content_type: str = None, limit: int = 50) -> List[Dict]:
        """Get pending content flags"""
        query = {"status": "pending"}
        
        if content_type:
            query['content_type'] = content_type
        
        return self.find_many(query, limit=limit, sort=[("severity", -1), ("created_at", 1)])
    
    def resolve_flag(self, flag_id: ObjectId, resolved_by: ObjectId, action_taken: str, notes: str = ""):
        """Resolve a content flag"""
        self.update_by_id(flag_id, {
            'status': 'resolved',
            'resolved_by': resolved_by,
            'resolved_at': datetime.now(),
            'action_taken': action_taken,
            'resolution_notes': notes
        })

class ModerationQueue(BaseModel):
    """Model for moderation queue"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'moderation_queue')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.moderation_queue
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate moderation queue data"""
        required_fields = ['content_type', 'content_id']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('status', 'pending')
        data.setdefault('priority', 'normal')
        data.setdefault('assigned_to', None)
        data.setdefault('auto_flagged', False)
        
        return data
    
    def add_to_queue(self, content_type: str, content_id: ObjectId, priority: str = "normal", 
                    reason: str = "", auto_flagged: bool = False) -> ObjectId:
        """Add content to moderation queue"""
        data = {
            'content_type': content_type,
            'content_id': content_id,
            'priority': priority,
            'reason': reason,
            'auto_flagged': auto_flagged
        }
        
        return self.create(data)
    
    def get_queue_items(self, status: str = "pending", assigned_to: ObjectId = None, limit: int = 50) -> List[Dict]:
        """Get items from moderation queue"""
        query = {"status": status}
        
        if assigned_to:
            query['assigned_to'] = assigned_to
        
        return self.find_many(query, limit=limit, sort=[("priority", -1), ("created_at", 1)])
    
    def assign_moderator(self, queue_id: ObjectId, moderator_id: ObjectId) -> bool:
        """Assign a moderator to a queue item"""
        return self.update_by_id(queue_id, {
            'assigned_to': moderator_id,
            'assigned_at': datetime.now(),
            'status': 'in_progress'
        })
    
    def complete_moderation(self, queue_id: ObjectId, moderator_id: ObjectId, action: str, notes: str = ""):
        """Complete moderation of a queue item"""
        self.update_by_id(queue_id, {
            'status': 'completed',
            'completed_by': moderator_id,
            'completed_at': datetime.now(),
            'action_taken': action,
            'moderation_notes': notes
        })

class UserAlert(BaseModel):
    """Enhanced model for user alerts/notifications"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'user_alerts')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.user_alerts
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate alert data"""
        required_fields = ['user_id', 'alert_name']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('active', True)
        data.setdefault('alert_type', 'keyword')
        data.setdefault('keywords', [])
        data.setdefault('categories', [])
        data.setdefault('trigger_count', 0)
        data.setdefault('notification_methods', ['email'])
        
        return data
    
    def get_user_alerts(self, user_id: ObjectId, active_only: bool = True) -> List[Dict]:
        """Get all alerts for a user"""
        query = {"user_id": user_id}
        if active_only:
            query["active"] = True
        
        return self.find_many(query, sort=[("created_at", -1)])
    
    def trigger_alert(self, alert_id: ObjectId, trigger_data: Dict = None):
        """Trigger an alert and update statistics"""
        update_data = {
            'last_triggered': datetime.now()
        }
        
        if trigger_data:
            update_data['last_trigger_data'] = trigger_data
        
        self.collection.update_one(
            {"_id": alert_id},
            {
                "$inc": {"trigger_count": 1},
                "$set": update_data
            }
        )

class UserSession(BaseModel):
    """Enhanced model for user sessions"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'user_sessions')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.user_sessions
    
    def create_session(self, user_id: ObjectId, expires_hours: int = 24, device_info: Dict = None) -> str:
        """Create a new user session with device tracking"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        session_data = {
            'user_id': user_id,
            'session_token': session_token,
            'expires_at': expires_at,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'device_info': device_info or {},
            'active': True
        }
        
        self.create(session_data)
        return session_token
    
    def get_session(self, session_token: str) -> Optional[Dict]:
        """Get active session by token"""
        return self.collection.find_one({
            "session_token": session_token,
            "expires_at": {"$gt": datetime.now()},
            "active": True
        })
    
    def update_activity(self, session_token: str, activity_data: Dict = None):
        """Update last activity for session"""
        update_data = {"last_activity": datetime.now()}
        
        if activity_data:
            update_data['last_activity_data'] = activity_data
        
        self.collection.update_one(
            {"session_token": session_token},
            {"$set": update_data}
        )
    
    def revoke_session(self, session_token: str) -> bool:
        """Revoke a session"""
        result = self.collection.update_one(
            {"session_token": session_token},
            {"$set": {"active": False, "revoked_at": datetime.now()}}
        )
        
        return result.modified_count > 0
    
    def revoke_all_user_sessions(self, user_id: ObjectId) -> int:
        """Revoke all sessions for a user"""
        result = self.collection.update_many(
            {"user_id": user_id, "active": True},
            {"$set": {"active": False, "revoked_at": datetime.now()}}
        )
        
        return result.modified_count
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        result = self.collection.delete_many({
            "expires_at": {"$lt": datetime.now()}
        })
        return result.deleted_count
    
    def get_user_sessions(self, user_id: ObjectId, active_only: bool = True) -> List[Dict]:
        """Get all sessions for a user"""
        query = {"user_id": user_id}
        if active_only:
            query["active"] = True
            query["expires_at"] = {"$gt": datetime.now()}
        
        return self.find_many(query, sort=[("last_activity", -1)])

class SystemSettings(BaseModel):
    """Model for system settings"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'system_settings')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.system_settings
    
    def get_setting(self, setting_key: str) -> Optional[Dict]:
        """Get a system setting"""
        return self.collection.find_one({"setting_key": setting_key})
    
    def get_setting_value(self, setting_key: str, default_value=None):
        """Get the value of a system setting"""
        setting = self.get_setting(setting_key)
        return setting.get('setting_value', default_value) if setting else default_value
    
    def update_setting(self, setting_key: str, setting_value, updated_by: str = "system"):
        """Update a system setting"""
        self.collection.update_one(
            {"setting_key": setting_key},
            {
                "$set": {
                    "setting_value": setting_value,
                    "updated_at": datetime.now(),
                    "updated_by": updated_by
                }
            },
            upsert=True
        )
    
    def get_settings_by_category(self, category: str) -> List[Dict]:
        """Get all settings in a category"""
        return self.find_many({"category": category})

class UserAnalytics(BaseModel):
    """Model for user analytics tracking"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'user_analytics')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.user_analytics
    
    def track_event(self, user_id: ObjectId, event_type: str, event_data: Dict = None, 
                   session_id: str = None) -> ObjectId:
        """Track a user event"""
        data = {
            'user_id': user_id,
            'event_type': event_type,
            'event_data': event_data or {},
            'session_id': session_id,
            'date': datetime.now().date(),
            'timestamp': datetime.now()
        }
        
        return self.create(data)
    
    def get_user_analytics(self, user_id: ObjectId, event_type: str = None, 
                          days: int = 30) -> List[Dict]:
        """Get analytics for a specific user"""
        query = {
            'user_id': user_id,
            'date': {'$gte': datetime.now().date() - timedelta(days=days)}
        }
        
        if event_type:
            query['event_type'] = event_type
        
        return self.find_many(query, sort=[('timestamp', -1)])
    
    def get_analytics_summary(self, days: int = 30) -> Dict:
        """Get analytics summary across all users"""
        pipeline = [
            {
                "$match": {
                    "date": {"$gte": datetime.now().date() - timedelta(days=days)}
                }
            },
            {
                "$group": {
                    "_id": "$event_type",
                    "count": {"$sum": 1},
                    "unique_users": {"$addToSet": "$user_id"}
                }
            },
            {
                "$project": {
                    "event_type": "$_id",
                    "count": 1,
                    "unique_users": {"$size": "$unique_users"}
                }
            }
        ]
        
        results = self.aggregate(pipeline)
        return {result['event_type']: result for result in results}

class NotificationQueue(BaseModel):
    """Model for notification queue"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'notification_queue')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.notification_queue
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate notification data"""
        required_fields = ['user_id', 'notification_type', 'content']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('status', 'pending')
        data.setdefault('priority', 'normal')
        data.setdefault('delivery_method', 'email')
        data.setdefault('scheduled_at', datetime.now())
        data.setdefault('retry_count', 0)
        data.setdefault('max_retries', 3)
        
        return data
    
    def queue_notification(self, user_id: ObjectId, notification_type: str, content: Dict,
                          delivery_method: str = 'email', priority: str = 'normal',
                          scheduled_at: datetime = None) -> ObjectId:
        """Queue a notification for delivery"""
        data = {
            'user_id': user_id,
            'notification_type': notification_type,
            'content': content,
            'delivery_method': delivery_method,
            'priority': priority,
            'scheduled_at': scheduled_at or datetime.now()
        }
        
        return self.create(data)
    
    def get_pending_notifications(self, delivery_method: str = None, limit: int = 100) -> List[Dict]:
        """Get pending notifications for delivery"""
        query = {
            'status': 'pending',
            'scheduled_at': {'$lte': datetime.now()}
        }
        
        if delivery_method:
            query['delivery_method'] = delivery_method
        
        return self.find_many(query, limit=limit, sort=[('priority', -1), ('scheduled_at', 1)])
    
    def mark_notification_sent(self, notification_id: ObjectId, delivery_status: str = 'sent',
                              delivery_details: Dict = None):
        """Mark notification as sent"""
        update_data = {
            'status': delivery_status,
            'sent_at': datetime.now()
        }
        
        if delivery_details:
            update_data['delivery_details'] = delivery_details
        
        self.update_by_id(notification_id, update_data)
    
    def mark_notification_failed(self, notification_id: ObjectId, error_message: str = ""):
        """Mark notification as failed and handle retry logic"""
        notification = self.find_by_id(notification_id)
        if not notification:
            return
        
        retry_count = notification.get('retry_count', 0) + 1
        max_retries = notification.get('max_retries', 3)
        
        if retry_count >= max_retries:
            # Mark as permanently failed
            self.update_by_id(notification_id, {
                'status': 'failed',
                'retry_count': retry_count,
                'error_message': error_message,
                'failed_at': datetime.now()
            })
        else:
            # Schedule for retry
            retry_delay = min(retry_count * 300, 3600)  # Exponential backoff, max 1 hour
            next_retry = datetime.now() + timedelta(seconds=retry_delay)
            
            self.update_by_id(notification_id, {
                'status': 'pending',
                'retry_count': retry_count,
                'scheduled_at': next_retry,
                'last_error': error_message
            })

class NotificationHistory(BaseModel):
    """Model for notification history"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'notification_history')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.notification_history
    
    def log_notification(self, user_id: ObjectId, notification_type: str, delivery_method: str,
                        delivery_status: str, content: Dict = None, delivery_details: Dict = None) -> ObjectId:
        """Log a sent notification"""
        data = {
            'user_id': user_id,
            'notification_type': notification_type,
            'delivery_method': delivery_method,
            'delivery_status': delivery_status,
            'content': content or {},
            'delivery_details': delivery_details or {},
            'sent_at': datetime.now()
        }
        
        return self.create(data)
    
    def get_user_notification_history(self, user_id: ObjectId, days: int = 30) -> List[Dict]:
        """Get notification history for a user"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.find_many(
            {
                'user_id': user_id,
                'sent_at': {'$gte': cutoff_date}
            },
            sort=[('sent_at', -1)]
        )
    
    def get_notification_statistics(self, days: int = 7) -> Dict:
        """Get notification delivery statistics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "sent_at": {"$gte": cutoff_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "delivery_method": "$delivery_method",
                        "delivery_status": "$delivery_status"
                    },
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = self.aggregate(pipeline)
        
        stats = {}
        for result in results:
            method = result['_id']['delivery_method']
            status = result['_id']['delivery_status']
            
            if method not in stats:
                stats[method] = {}
            
            stats[method][status] = result['count']
        
        return stats

class ExportRequest(BaseModel):
    """Model for export requests"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'export_requests')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.export_requests
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate export request data"""
        required_fields = ['user_id', 'export_type', 'filters']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('status', 'pending')
        data.setdefault('format', 'csv')
        data.setdefault('compression', 'none')
        data.setdefault('priority', 'normal')
        
        return data
    
    def create_export_request(self, user_id: ObjectId, export_type: str, filters: Dict,
                             format: str = 'csv', compression: str = 'none') -> ObjectId:
        """Create a new export request"""
        data = {
            'user_id': user_id,
            'export_type': export_type,
            'filters': filters,
            'format': format,
            'compression': compression,
            'requested_at': datetime.now()
        }
        
        return self.create(data)
    
    def get_pending_exports(self, limit: int = 50) -> List[Dict]:
        """Get pending export requests"""
        return self.find_many(
            {'status': 'pending'},
            limit=limit,
            sort=[('priority', -1), ('requested_at', 1)]
        )
    
    def get_user_exports(self, user_id: ObjectId, limit: int = 20) -> List[Dict]:
        """Get export requests for a user"""
        return self.find_many(
            {'user_id': user_id},
            limit=limit,
            sort=[('requested_at', -1)]
        )
    
    def update_export_status(self, export_id: ObjectId, status: str, file_path: str = None,
                            file_size: int = None, record_count: int = None, error_message: str = None):
        """Update export request status"""
        update_data = {'status': status}
        
        if status == 'completed':
            update_data.update({
                'completed_at': datetime.now(),
                'file_path': file_path,
                'file_size_bytes': file_size,
                'record_count': record_count,
                'download_expires': datetime.now() + timedelta(days=7)
            })
        elif status == 'failed':
            update_data.update({
                'failed_at': datetime.now(),
                'error_message': error_message
            })
        elif status == 'processing':
            update_data['started_at'] = datetime.now()
        
        self.update_by_id(export_id, update_data)

class FeatureFlag(BaseModel):
    """Model for feature flags"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'feature_flags')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.feature_flags
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Validate feature flag data"""
        required_fields = ['flag_name', 'enabled']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        data.setdefault('description', '')
        data.setdefault('target_users', [])
        data.setdefault('rollout_percentage', 100)
        
        return data
    
    def is_feature_enabled(self, flag_name: str, user_id: ObjectId = None, username: str = None) -> bool:
        """Check if a feature is enabled for a user"""
        flag = self.collection.find_one({'flag_name': flag_name})
        
        if not flag or not flag.get('enabled', False):
            return False
        
        # Check if specific users are targeted
        target_users = flag.get('target_users', [])
        if target_users:
            if username and username in target_users:
                return True
            if user_id and str(user_id) in target_users:
                return True
            return False
        
        # Check rollout percentage
        rollout_percentage = flag.get('rollout_percentage', 100)
        if rollout_percentage < 100:
            # Use user_id hash for consistent rollout
            user_hash = hash(str(user_id)) % 100 if user_id else 0
            return user_hash < rollout_percentage
        
        return True
    
    def update_feature_flag(self, flag_name: str, enabled: bool = None, target_users: List[str] = None,
                           rollout_percentage: int = None, description: str = None):
        """Update a feature flag"""
        update_data = {'updated_at': datetime.now()}
        
        if enabled is not None:
            update_data['enabled'] = enabled
        if target_users is not None:
            update_data['target_users'] = target_users
        if rollout_percentage is not None:
            update_data['rollout_percentage'] = rollout_percentage
        if description is not None:
            update_data['description'] = description
        
        self.collection.update_one(
            {'flag_name': flag_name},
            {'$set': update_data},
            upsert=True
        )
    
    def get_all_flags(self) -> List[Dict]:
        """Get all feature flags"""
        return self.find_many(sort=[('flag_name', 1)])

class SystemHealth(BaseModel):
    """Model for system health monitoring"""
    
    def __init__(self):
        super().__init__(DatabaseManager(), 'system_health')
    
    @property
    def collection(self):
        return self.db_manager.web_app_db.system_health
    
    def record_health_check(self, component: str, status: str, metrics: Dict = None,
                           error_message: str = None) -> ObjectId:
        """Record a health check result"""
        data = {
            'component': component,
            'status': status,
            'metrics': metrics or {},
            'timestamp': datetime.now()
        }
        
        if error_message:
            data['error_message'] = error_message
        
        return self.create(data)
    
    def get_latest_health_status(self) -> Dict:
        """Get latest health status for all components"""
        pipeline = [
            {
                "$sort": {"timestamp": -1}
            },
            {
                "$group": {
                    "_id": "$component",
                    "latest_status": {"$first": "$status"},
                    "latest_timestamp": {"$first": "$timestamp"},
                    "latest_metrics": {"$first": "$metrics"},
                    "latest_error": {"$first": "$error_message"}
                }
            }
        ]
        
        results = self.aggregate(pipeline)
        
        health_status = {}
        overall_healthy = True
        
        for result in results:
            component = result['_id']
            status = result['latest_status']
            
            health_status[component] = {
                'status': status,
                'timestamp': result['latest_timestamp'],
                'metrics': result.get('latest_metrics', {}),
                'error_message': result.get('latest_error')
            }
            
            if status != 'healthy':
                overall_healthy = False
        
        return {
            'overall_status': 'healthy' if overall_healthy else 'unhealthy',
            'components': health_status,
            'last_check': max([comp['timestamp'] for comp in health_status.values()]) if health_status else None
        }
    
    def get_health_history(self, component: str = None, hours: int = 24) -> List[Dict]:
        """Get health check history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        query = {'timestamp': {'$gte': cutoff_time}}
        
        if component:
            query['component'] = component
        
        return self.find_many(query, sort=[('timestamp', -1)])

# Export all models
__all__ = [
    'UserType', 'User', 'UserBookmark', 'UserFollow', 'UserReport', 'Post',
    'ContentFlag', 'ModerationQueue', 'UserAlert', 'UserSession', 'SystemSettings',
    'UserAnalytics', 'NotificationQueue', 'NotificationHistory', 'ExportRequest',
    'FeatureFlag', 'SystemHealth'
]