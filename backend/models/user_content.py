"""
User Content model for the Global Protest Tracker
Handles photos, reports, and other stuff users post
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from bson import ObjectId

from .protest import BaseModel, ValidationError


class UserContentModel(BaseModel):
    """Handles user posts, photos, reports, and other content."""

    def __init__(self):
        super().__init__()
        self.collection = self.db.user_content

    def create(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new user content (photo, report, etc.).

        Args:
            content_data: The content info including user_id, type, and actual content

        Returns:
            The created content

        Raises:
            ValidationError: If something's missing or invalid
        """
        # Make sure we have the essentials
        required_fields = ['user_id', 'content_type', 'content']
        for field in required_fields:
            if field not in content_data or not content_data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Check if it's a valid content type
        valid_types = ['report', 'photo', 'video', 'update', 'comment']
        if content_data['content_type'] not in valid_types:
            raise ValidationError(f"Invalid content_type. Must be one of: {valid_types}")
        
        # Prepare content document
        content_doc = self._prepare_for_insert(content_data.copy())
        
        # Set default values
        content_doc.setdefault('status', 'pending')  # pending, approved, rejected
        content_doc.setdefault('verified', False)
        content_doc.setdefault('moderated', False)
        content_doc.setdefault('media_urls', [])
        content_doc.setdefault('tags', [])
        content_doc.setdefault('likes', 0)
        content_doc.setdefault('reports', 0)
        content_doc.setdefault('visibility', 'public')  # public, private, restricted
        
        # Add location if provided
        if 'location' in content_data:
            if isinstance(content_data['location'], str):
                # Convert string location to structured format
                location_parts = content_data['location'].split(',')
                content_doc['location'] = {
                    'city': location_parts[0].strip() if len(location_parts) > 0 else '',
                    'country': location_parts[-1].strip() if len(location_parts) > 1 else '',
                    'address': content_data['location'],
                    'coordinates': content_data.get('coordinates', [])
                }
        
        # Insert document
        result = self.collection.insert_one(content_doc)
        content_doc['_id'] = result.inserted_id
        
        return self._serialize_object_id(content_doc)
    
    def find_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Find content by ID."""
        try:
            if ObjectId.is_valid(content_id):
                doc = self.collection.find_one({'_id': ObjectId(content_id)})
            else:
                doc = self.collection.find_one({'content_id': content_id})
            
            return self._serialize_object_id(doc) if doc else None
        except Exception:
            return None
    
    def find_by_user(self, user_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find all content by a specific user."""
        query = {'user_id': user_id}
        
        if content_type:
            query['content_type'] = content_type
        
        cursor = self.collection.find(query).sort('created_at', -1)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def find_by_protest(self, protest_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find all content related to a specific protest."""
        query = {'protest_id': protest_id, 'status': 'approved'}
        
        if content_type:
            query['content_type'] = content_type
        
        cursor = self.collection.find(query).sort('created_at', -1)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def find_pending_moderation(self) -> List[Dict[str, Any]]:
        """Find all content pending moderation."""
        cursor = self.collection.find({'status': 'pending'}).sort('created_at', 1)
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def find_public_content(self, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """Find public approved content."""
        cursor = self.collection.find({
            'status': 'approved',
            'visibility': 'public'
        }).sort('created_at', -1).skip(skip).limit(limit)
        
        return [self._serialize_object_id(doc) for doc in cursor]
    
    def update(self, content_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update existing content.
        
        Args:
            content_id: Content ID to update
            update_data: Fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate status if being updated
            if 'status' in update_data:
                valid_statuses = ['pending', 'approved', 'rejected']
                if update_data['status'] not in valid_statuses:
                    raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")
            
            # Validate visibility if being updated
            if 'visibility' in update_data:
                valid_visibility = ['public', 'private', 'restricted']
                if update_data['visibility'] not in valid_visibility:
                    raise ValidationError(f"Invalid visibility. Must be one of: {valid_visibility}")
            
            update_data = self._prepare_for_update(update_data)
            
            if ObjectId.is_valid(content_id):
                result = self.collection.update_one(
                    {'_id': ObjectId(content_id)},
                    {'$set': update_data}
                )
            else:
                result = self.collection.update_one(
                    {'content_id': content_id},
                    {'$set': update_data}
                )
            
            return result.modified_count > 0
        except Exception:
            return False
    
    def moderate_content(self, content_id: str, status: str, moderator_id: str, notes: str = "") -> bool:
        """
        Moderate content (approve/reject).
        
        Args:
            content_id: Content ID to moderate
            status: New status ('approved' or 'rejected')
            moderator_id: ID of the moderator
            notes: Optional moderation notes
            
        Returns:
            True if moderation successful, False otherwise
        """
        if status not in ['approved', 'rejected']:
            return False
        
        moderation_data = {
            'status': status,
            'moderated': True,
            'moderated_at': datetime.utcnow(),
            'moderator_id': moderator_id,
            'moderation_notes': notes
        }
        
        return self.update(content_id, moderation_data)
    
    def like_content(self, content_id: str, user_id: str) -> bool:
        """
        Like/unlike content.
        
        Args:
            content_id: Content ID to like
            user_id: User ID who is liking
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if user already liked this content
            existing_like = self.db.content_likes.find_one({
                'content_id': content_id,
                'user_id': user_id
            })
            
            if existing_like:
                # Unlike - remove like and decrement counter
                self.db.content_likes.delete_one({
                    'content_id': content_id,
                    'user_id': user_id
                })
                
                if ObjectId.is_valid(content_id):
                    self.collection.update_one(
                        {'_id': ObjectId(content_id)},
                        {'$inc': {'likes': -1}}
                    )
                else:
                    self.collection.update_one(
                        {'content_id': content_id},
                        {'$inc': {'likes': -1}}
                    )
            else:
                # Like - add like and increment counter
                self.db.content_likes.insert_one({
                    'content_id': content_id,
                    'user_id': user_id,
                    'created_at': datetime.utcnow()
                })
                
                if ObjectId.is_valid(content_id):
                    self.collection.update_one(
                        {'_id': ObjectId(content_id)},
                        {'$inc': {'likes': 1}}
                    )
                else:
                    self.collection.update_one(
                        {'content_id': content_id},
                        {'$inc': {'likes': 1}}
                    )
            
            return True
        except Exception:
            return False
    
    def report_content(self, content_id: str, reporter_id: str, reason: str) -> bool:
        """
        Report content for moderation.
        
        Args:
            content_id: Content ID to report
            reporter_id: User ID who is reporting
            reason: Reason for reporting
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add report record
            self.db.content_reports.insert_one({
                'content_id': content_id,
                'reporter_id': reporter_id,
                'reason': reason,
                'created_at': datetime.utcnow(),
                'status': 'pending'
            })
            
            # Increment report counter
            if ObjectId.is_valid(content_id):
                self.collection.update_one(
                    {'_id': ObjectId(content_id)},
                    {'$inc': {'reports': 1}}
                )
            else:
                self.collection.update_one(
                    {'content_id': content_id},
                    {'$inc': {'reports': 1}}
                )
            
            return True
        except Exception:
            return False
    
    def delete(self, content_id: str) -> bool:
        """
        Delete content (soft delete by setting status to 'deleted').
        
        Args:
            content_id: Content ID to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        return self.update(content_id, {
            'status': 'deleted',
            'deleted_at': datetime.utcnow()
        })
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """Get content statistics."""
        pipeline = [
            {
                '$group': {
                    '_id': '$content_type',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        type_counts = {doc['_id']: doc['count'] for doc in self.collection.aggregate(pipeline)}
        
        status_pipeline = [
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        status_counts = {doc['_id']: doc['count'] for doc in self.collection.aggregate(status_pipeline)}
        
        total_content = self.collection.count_documents({})
        pending_moderation = self.collection.count_documents({'status': 'pending'})
        
        return {
            'total_content': total_content,
            'pending_moderation': pending_moderation,
            'type_breakdown': type_counts,
            'status_breakdown': status_counts,
            'last_updated': datetime.utcnow().isoformat()
        }
