from abc import ABC, abstractmethod
from datetime import datetime
from bson import ObjectId
from typing import Dict, List, Optional, Any, Union
import logging

from .database import DatabaseManager

class BaseModel(ABC):
    """Enhanced base model class for MongoDB documents"""
    
    def __init__(self, db_manager: DatabaseManager, collection_name: str):
        self.db_manager = db_manager
        self.collection_name = collection_name
        self._collection = None
    
    @property
    @abstractmethod
    def collection(self):
        """Return the MongoDB collection"""
        pass
    
    def create(self, data: Dict) -> ObjectId:
        """Create a new document"""
        try:
            # Add timestamps
            now = datetime.now()
            data['created_at'] = now
            data['updated_at'] = now
            
            # Validate data
            validated_data = self.validate_create_data(data)
            
            result = self.collection.insert_one(validated_data)
            logging.info(f"Created {self.collection_name} with ID: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            logging.error(f"Error creating {self.collection_name}: {e}")
            raise
    
    def create_many(self, data_list: List[Dict]) -> List[ObjectId]:
        """Create multiple documents"""
        try:
            now = datetime.now()
            validated_data = []
            
            for data in data_list:
                data['created_at'] = now
                data['updated_at'] = now
                validated_data.append(self.validate_create_data(data))
            
            result = self.collection.insert_many(validated_data)
            logging.info(f"Created {len(result.inserted_ids)} {self.collection_name} documents")
            return result.inserted_ids
            
        except Exception as e:
            logging.error(f"Error creating multiple {self.collection_name}: {e}")
            raise
    
    def find_by_id(self, doc_id: Union[ObjectId, str]) -> Optional[Dict]:
        """Find document by ID"""
        try:
            if isinstance(doc_id, str):
                doc_id = ObjectId(doc_id)
            return self.collection.find_one({"_id": doc_id})
        except Exception as e:
            logging.error(f"Error finding {self.collection_name} by ID: {e}")
            return None
    
    def find_one(self, query: Dict) -> Optional[Dict]:
        """Find one document by query"""
        try:
            return self.collection.find_one(query)
        except Exception as e:
            logging.error(f"Error finding one {self.collection_name}: {e}")
            return None
    
    def find_many(self, query: Dict = None, limit: int = 100, sort: List = None, skip: int = 0) -> List[Dict]:
        """Find multiple documents with pagination"""
        try:
            query = query or {}
            cursor = self.collection.find(query)
            
            if sort:
                cursor = cursor.sort(sort)
            
            if skip > 0:
                cursor = cursor.skip(skip)
                
            return list(cursor.limit(limit))
            
        except Exception as e:
            logging.error(f"Error finding {self.collection_name}: {e}")
            return []
    
    def update_by_id(self, doc_id: Union[ObjectId, str], update_data: Dict, use_set: bool = True) -> bool:
        """Update document by ID"""
        try:
            if isinstance(doc_id, str):
                doc_id = ObjectId(doc_id)
                
            # Add update timestamp
            if use_set:
                update_data['updated_at'] = datetime.now()
                update_operation = {"$set": update_data}
            else:
                # Allow custom update operations like $inc, $push, etc.
                update_operation = update_data
                if '$set' not in update_operation:
                    update_operation['$set'] = {'updated_at': datetime.now()}
                else:
                    update_operation['$set']['updated_at'] = datetime.now()
            
            result = self.collection.update_one(
                {"_id": doc_id}, 
                update_operation
            )
            
            success = result.modified_count > 0
            if success:
                logging.info(f"Updated {self.collection_name} with ID: {doc_id}")
            return success
            
        except Exception as e:
            logging.error(f"Error updating {self.collection_name}: {e}")
            return False
    
    def update_many(self, query: Dict, update_data: Dict, use_set: bool = True) -> int:
        """Update multiple documents"""
        try:
            if use_set:
                update_data['updated_at'] = datetime.now()
                update_operation = {"$set": update_data}
            else:
                update_operation = update_data
                if '$set' not in update_operation:
                    update_operation['$set'] = {'updated_at': datetime.now()}
                else:
                    update_operation['$set']['updated_at'] = datetime.now()
            
            result = self.collection.update_many(query, update_operation)
            logging.info(f"Updated {result.modified_count} {self.collection_name} documents")
            return result.modified_count
            
        except Exception as e:
            logging.error(f"Error updating multiple {self.collection_name}: {e}")
            return 0
    
    def delete_by_id(self, doc_id: Union[ObjectId, str]) -> bool:
        """Delete document by ID"""
        try:
            if isinstance(doc_id, str):
                doc_id = ObjectId(doc_id)
                
            result = self.collection.delete_one({"_id": doc_id})
            success = result.deleted_count > 0
            
            if success:
                logging.info(f"Deleted {self.collection_name} with ID: {doc_id}")
            return success
            
        except Exception as e:
            logging.error(f"Error deleting {self.collection_name}: {e}")
            return False
    
    def delete_many(self, query: Dict) -> int:
        """Delete multiple documents"""
        try:
            result = self.collection.delete_many(query)
            logging.info(f"Deleted {result.deleted_count} {self.collection_name} documents")
            return result.deleted_count
            
        except Exception as e:
            logging.error(f"Error deleting multiple {self.collection_name}: {e}")
            return 0
    
    def validate_create_data(self, data: Dict) -> Dict:
        """Override this method to add validation"""
        return data
    
    def count(self, query: Dict = None) -> int:
        """Count documents matching query"""
        try:
            query = query or {}
            return self.collection.count_documents(query)
        except Exception as e:
            logging.error(f"Error counting {self.collection_name}: {e}")
            return 0
    
    def aggregate(self, pipeline: List[Dict]) -> List[Dict]:
        """Execute aggregation pipeline"""
        try:
            return list(self.collection.aggregate(pipeline))
        except Exception as e:
            logging.error(f"Error running aggregation on {self.collection_name}: {e}")
            return []