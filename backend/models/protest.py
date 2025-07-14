"""
MongoDB models for the Global Protest Tracker
This file handles all the database stuff for protests and sets up the connection
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from bson import ObjectId
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError
import os


class ValidationError(Exception):
    """Custom validation error for our models."""
    pass


class DatabaseConnection:
    """Manages our MongoDB connection. Only creates one connection that everyone shares."""

    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()

    def connect(self):
        """Connect to MongoDB and set up all the indexes we need."""
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/protest_tracker')
        self._client = MongoClient(mongodb_uri)

        # Figure out the database name from the connection string
        if '/' in mongodb_uri.split('://')[-1]:
            db_name = mongodb_uri.split('/')[-1]
        else:
            db_name = 'protest_tracker'

        self._db = self._client[db_name]

        # Set up all our database indexes for fast queries
        self._create_indexes()

    def _create_indexes(self):
        """Set up database indexes to make queries fast."""
        # Protest indexes - these make location and search queries super fast
        protests = self._db.protests
        protests.create_index([("location.coordinates", "2dsphere")])  # For map searches
        protests.create_index([("start_date", DESCENDING)])  # Sort by date
        protests.create_index([("status", ASCENDING)])  # Filter by status
        protests.create_index([("categories", ASCENDING)])  # Filter by category
        protests.create_index([("title", TEXT), ("description", TEXT)])  # Text search

        # User indexes - make sure emails and usernames are unique
        users = self._db.users
        users.create_index([("email", ASCENDING)], unique=True)
        users.create_index([("username", ASCENDING)], unique=True)

        # Alert indexes - for finding user alerts quickly
        alerts = self._db.alerts
        alerts.create_index([("user_id", ASCENDING)])
        alerts.create_index([("keywords", ASCENDING)])

        # User content indexes - for finding posts by user or protest
        user_content = self._db.user_content
        user_content.create_index([("user_id", ASCENDING)])
        user_content.create_index([("protest_id", ASCENDING)])
        user_content.create_index([("created_at", DESCENDING)])

    @property
    def db(self):
        """Get the database connection, creating it if needed."""
        if self._db is None:
            self.connect()
        return self._db

    def close(self):
        """Clean up the database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None


class BaseModel:
    """Base class that all our models inherit from. Has common database stuff."""

    def __init__(self):
        self.db_connection = DatabaseConnection()
        self.db = self.db_connection.db

    def _serialize_object_id(self, doc: Dict) -> Dict:
        """Convert MongoDB's ObjectId to a string so we can send it as JSON."""
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc

    def _prepare_for_insert(self, data: Dict) -> Dict:
        """Add timestamps when creating new records."""
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        return data

    def _prepare_for_update(self, data: Dict) -> Dict:
        """Update the timestamp when modifying records."""
        data['updated_at'] = datetime.utcnow()
        return data


class ProtestModel(BaseModel):
    """Handles all the database operations for protests."""

    def __init__(self):
        super().__init__()
        self.collection = self.db.protests

    def create(self, protest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new protest in the database.

        Args:
            protest_data: All the protest info (title, description, location, etc.)

        Returns:
            The created protest with its new database ID

        Raises:
            ValidationError: If something's missing or wrong with the data
        """
        # Make sure we have all the required info
        required_fields = ['title', 'description', 'location', 'start_date', 'categories']
        for field in required_fields:
            if field not in protest_data or not protest_data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Get the data ready for the database
        protest_doc = self._prepare_for_insert(protest_data.copy())

        # Fill in some sensible defaults
        protest_doc.setdefault('status', 'planned')
        protest_doc.setdefault('participant_count', 0)
        protest_doc.setdefault('verified', False)
        protest_doc.setdefault('source', 'user_submitted')
        protest_doc.setdefault('media_urls', [])
        protest_doc.setdefault('tags', [])

        # Validate and format location
        if isinstance(protest_doc['location'], str):
            # Convert string location to structured format
            location_parts = protest_doc['location'].split(',')
            protest_doc['location'] = {
                'city': location_parts[0].strip() if len(location_parts) > 0 else '',
                'country': location_parts[-1].strip() if len(location_parts) > 1 else '',
                'address': protest_doc['location'],
                'coordinates': protest_doc.get('coordinates', [])
            }

        # Validate date format
        if isinstance(protest_doc['start_date'], str):
            try:
                datetime.fromisoformat(protest_doc['start_date'].replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError("Invalid start_date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")

        # Insert document
        result = self.collection.insert_one(protest_doc)
        protest_doc['_id'] = result.inserted_id

        return self._serialize_object_id(protest_doc)

    def find_by_id(self, protest_id: str) -> Optional[Dict[str, Any]]:
        """Find protest by ID."""
        try:
            if ObjectId.is_valid(protest_id):
                doc = self.collection.find_one({'_id': ObjectId(protest_id)})
            else:
                # Support legacy string IDs from test data
                doc = self.collection.find_one({'protest_id': protest_id})

            return self._serialize_object_id(doc) if doc else None
        except Exception:
            return None

    def find_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find protests with optional filters.

        Args:
            filters: Dictionary of filters
                - location: City name to filter by
                - cause: Cause/category to filter by
                - start_date: Start date for date range
                - end_date: End date for date range
                - status: Protest status
                - coordinates: [longitude, latitude] for geo search
                - radius: Search radius in meters (default 10000)

        Returns:
            List of protest documents
        """
        query = {}

        if filters:
            # Location filter (city name)
            if 'location' in filters and filters['location']:
                city_filter = filters['location'].split(',')[0].strip()
                query['location.city'] = {'$regex': city_filter, '$options': 'i'}

            # Category/cause filter
            if 'cause' in filters and filters['cause']:
                query['categories'] = {'$in': [filters['cause']]}

            # Date range filters
            if 'start_date' in filters and filters['start_date']:
                query['start_date'] = {'$gte': filters['start_date']}

            if 'end_date' in filters and filters['end_date']:
                if 'start_date' not in query:
                    query['start_date'] = {}
                query['start_date']['$lte'] = filters['end_date']

            # Status filter
            if 'status' in filters and filters['status']:
                query['status'] = filters['status']

            # Geospatial search
            if 'coordinates' in filters and filters['coordinates']:
                radius = filters.get('radius', 10000)  # Default 10km radius
                query['location.coordinates'] = {
                    '$near': {
                        '$geometry': {
                            'type': 'Point',
                            'coordinates': filters['coordinates']
                        },
                        '$maxDistance': radius
                    }
                }

        # Execute query with sorting
        cursor = self.collection.find(query).sort('start_date', DESCENDING)

        return [self._serialize_object_id(doc) for doc in cursor]

    def search(self, keyword: str = "") -> List[Dict[str, Any]]:
        """
        Search protests by keyword using text search.

        Args:
            keyword: Search term for title, description, and categories

        Returns:
            List of matching protest documents
        """
        if not keyword:
            return self.find_with_filters()

        # Use MongoDB text search
        query = {'$text': {'$search': keyword}}
        cursor = self.collection.find(query).sort('start_date', DESCENDING)

        return [self._serialize_object_id(doc) for doc in cursor]

    def update(self, protest_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing protest.

        Args:
            protest_id: Protest ID to update
            update_data: Fields to update

        Returns:
            True if update successful, False otherwise
        """
        try:
            update_data = self._prepare_for_update(update_data)

            if ObjectId.is_valid(protest_id):
                result = self.collection.update_one(
                    {'_id': ObjectId(protest_id)},
                    {'$set': update_data}
                )
            else:
                result = self.collection.update_one(
                    {'protest_id': protest_id},
                    {'$set': update_data}
                )

            return result.modified_count > 0
        except Exception:
            return False

    def delete(self, protest_id: str) -> bool:
        """
        Delete a protest (soft delete by setting status to 'deleted').

        Args:
            protest_id: Protest ID to delete

        Returns:
            True if deletion successful, False otherwise
        """
        return self.update(protest_id, {'status': 'deleted', 'deleted_at': datetime.utcnow()})

    def get_statistics(self) -> Dict[str, Any]:
        """Get protest statistics."""
        pipeline = [
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            }
        ]

        status_counts = {doc['_id']: doc['count'] for doc in self.collection.aggregate(pipeline)}

        total_protests = self.collection.count_documents({})
        total_participants = self.collection.aggregate([
            {'$group': {'_id': None, 'total': {'$sum': '$participant_count'}}}
        ])

        participant_sum = next(total_participants, {}).get('total', 0)

        return {
            'total_protests': total_protests,
            'total_participants': participant_sum,
            'status_breakdown': status_counts,
            'last_updated': datetime.utcnow().isoformat()
        }
