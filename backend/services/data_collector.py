import json
import hashlib
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import schedule
from bson import ObjectId

from dotenv import load_dotenv
load_dotenv()

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing models
from models.data_collection_models import (
    DataSource, RawProtestData, Protest, ScrapingJob, ProtestAnalytics
)
from models.system_monitoring_models import (
    ErrorLog, WorkerStatus
)
from models.api_health_models import (
    ApiRateLimit, ServiceHealth, CollectionMetrics
)
from models.config_models import ServiceConfig, GeocodingCache, CategoryMapping

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingQueue:
    """Model for managing processing queue"""
    
    def __init__(self):
        from pymongo import MongoClient
        self.client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        self.collection = self.client['protest_data_collection'].processing_queue
    
    def create(self, queue_data: Dict) -> ObjectId:
        """Create new queue item"""
        queue_data.update({
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": "pending",
            "retry_count": queue_data.get("retry_count", 0),
            "assigned_worker": None,
            "processing_started_at": None
        })
        return self.collection.insert_one(queue_data).inserted_id
    
    def get_pending_items(self, processing_type: str = None, limit: int = 50) -> List[Dict]:
        """Get pending items from queue"""
        query = {"status": "pending"}
        if processing_type:
            query["processing_type"] = processing_type
        
        return list(self.collection.find(query)
                   .sort([("priority", -1), ("created_at", 1)])
                   .limit(limit))
    
    def update_status(self, queue_id: ObjectId, status: str, **kwargs) -> bool:
        """Update queue item status"""
        update_data = {"status": status, "updated_at": datetime.now()}
        
        if status == "processing":
            update_data["processing_started_at"] = datetime.now()
        elif status in ["completed", "failed_permanent"]:
            update_data["processing_completed_at"] = datetime.now()
        
        update_data.update(kwargs)
        
        result = self.collection.update_one(
            {"_id": queue_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def get_statistics(self) -> Dict:
        """Get queue statistics"""
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        stats = {doc["_id"]: doc["count"] for doc in self.collection.aggregate(pipeline)}
        return {
            "pending": stats.get("pending", 0),
            "processing": stats.get("processing", 0),
            "completed": stats.get("completed", 0),
            "failed": stats.get("failed_permanent", 0),
            "retry": stats.get("failed_retry", 0),
            "total": sum(stats.values())
        }


class ProcessingResults:
    """Model for storing processing results"""
    
    def __init__(self):
        from pymongo import MongoClient
        self.client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        self.collection = self.client['protest_data_collection'].processing_results
    
    def create(self, result_data: Dict) -> ObjectId:
        """Create processing result record"""
        result_data.update({
            "created_at": datetime.now()
        })
        return self.collection.insert_one(result_data).inserted_id
    
    def get_results_by_raw_data_id(self, raw_data_id: ObjectId) -> List[Dict]:
        """Get all processing results for a raw data record"""
        return list(self.collection.find({"raw_data_id": raw_data_id})
                   .sort("created_at", -1))


class DataLineage:
    """Model for tracking data lineage and transformations"""
    
    def __init__(self):
        from pymongo import MongoClient
        self.client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        self.collection = self.client['protest_data_collection'].data_lineage
    
    def create(self, lineage_data: Dict) -> ObjectId:
        """Create new lineage record"""
        lineage_data.update({
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "final_protest_id": None,
            "transformation_steps": lineage_data.get("transformation_steps", []),
            "data_quality_flags": lineage_data.get("data_quality_flags", []),
            "processing_notes": lineage_data.get("processing_notes", [])
        })
        return self.collection.insert_one(lineage_data).inserted_id
    
    def update_final_protest_id(self, lineage_id: ObjectId, protest_id: ObjectId) -> bool:
        """Update with final protest ID"""
        result = self.collection.update_one(
            {"_id": lineage_id},
            {
                "$set": {
                    "final_protest_id": protest_id,
                    "updated_at": datetime.now()
                }
            }
        )
        return result.modified_count > 0
    
    def add_transformation_step(self, lineage_id: ObjectId, step_data: Dict) -> bool:
        """Add transformation step to lineage"""
        step_data["timestamp"] = datetime.now()
        
        result = self.collection.update_one(
            {"_id": lineage_id},
            {
                "$push": {"transformation_steps": step_data},
                "$set": {"updated_at": datetime.now()}
            }
        )
        return result.modified_count > 0
    
    def add_quality_flag(self, lineage_id: ObjectId, flag_data: Dict) -> bool:
        """Add data quality flag"""
        flag_data["timestamp"] = datetime.now()
        
        result = self.collection.update_one(
            {"_id": lineage_id},
            {
                "$push": {"data_quality_flags": flag_data},
                "$set": {"updated_at": datetime.now()}
            }
        )
        return result.modified_count > 0
    
    def get_lineage_by_protest_id(self, protest_id: ObjectId) -> Optional[Dict]:
        """Get lineage record for a protest"""
        return self.collection.find_one({"final_protest_id": protest_id})


class ValidationRules:
    """Model for managing validation rules"""
    
    def __init__(self):
        from pymongo import MongoClient
        self.client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        self.collection = self.client['protest_data_collection'].validation_rules
    
    def get_active_rules(self) -> List[Dict]:
        """Get all active validation rules"""
        return list(self.collection.find({"active": True}).sort("priority", -1))
    
    def create_default_rules(self):
        """Create default validation rules"""
        default_rules = [
            {
                "rule_name": "title_length_check",
                "field_name": "title",
                "validation_type": "length",
                "validation_config": {"min_length": 10, "max_length": 500},
                "active": True,
                "severity": "critical",
                "error_message": "Title must be between 10 and 500 characters",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "rule_name": "location_required",
                "field_name": "location_description",
                "validation_type": "required",
                "validation_config": {},
                "active": True,
                "severity": "critical",
                "error_message": "Location description is required",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "rule_name": "coordinates_valid",
                "field_name": "location.coordinates",
                "validation_type": "coordinates",
                "validation_config": {"allow_zero": False},
                "active": True,
                "severity": "warning",
                "error_message": "Invalid or zero coordinates detected",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "rule_name": "date_reasonable",
                "field_name": "start_date",
                "validation_type": "date_range",
                "validation_config": {
                    "min_date": (datetime.now() - timedelta(days=365)).isoformat(),
                    "max_date": (datetime.now() + timedelta(days=365)).isoformat()
                },
                "active": True,
                "severity": "warning",
                "error_message": "Date must be within reasonable range (1 year ago to 1 year future)",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "rule_name": "description_quality",
                "field_name": "description",
                "validation_type": "text_quality",
                "validation_config": {"min_words": 5, "max_repetition": 0.5},
                "active": True,
                "severity": "warning",
                "error_message": "Description quality is poor",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        # Insert rules that don't exist
        for rule in default_rules:
            existing = self.collection.find_one({"rule_name": rule["rule_name"]})
            if not existing:
                self.collection.insert_one(rule)
                logger.info(f"Created validation rule: {rule['rule_name']}")


class GeocodingService:
    """Enhanced geocoding service with multiple providers and caching"""
    
    def __init__(self):
        self.geocoding_cache = GeocodingCache()
        self.api_keys = {
            'opencage': os.getenv('OPENCAGE_API_KEY'),
            'mapbox': os.getenv('MAPBOX_API_KEY'),
            'google': os.getenv('GOOGLE_GEOCODING_API_KEY')
        }
        self.default_provider = 'opencage'  # Free tier available
    
    def geocode_location(self, location_description: str) -> Dict:
        """Geocode location with caching and fallback providers"""
        try:
            # Normalize location string
            normalized_location = self._normalize_location_string(location_description)
            
            # Check cache first
            cached_result = self.geocoding_cache.get_cached_location(normalized_location)
            if cached_result:
                self.geocoding_cache.increment_hit_count(cached_result['_id'])
                return {
                    "success": True,
                    "location": {
                        "type": "Point",
                        "coordinates": cached_result['coordinates']['coordinates']
                    },
                    "confidence": cached_result['confidence'],
                    "country": cached_result.get('country', ''),
                    "from_cache": True,
                    "provider": cached_result.get('geocoding_service', 'cache')
                }
            
            # Try geocoding providers in order
            providers = ['opencage', 'mapbox', 'google']
            
            for provider in providers:
                if not self.api_keys.get(provider):
                    continue
                
                try:
                    result = self._geocode_with_provider(location_description, provider)
                    if result['success']:
                        # Cache successful result
                        self._cache_geocoding_result(
                            location_description, 
                            normalized_location, 
                            result, 
                            provider
                        )
                        return result
                except Exception as e:
                    logger.warning(f"Geocoding failed with {provider}: {e}")
                    continue
            
            # All providers failed
            return {
                "success": False,
                "error": "All geocoding providers failed",
                "location": {"type": "Point", "coordinates": [0.0, 0.0]},
                "confidence": 0.0
            }
            
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return {
                "success": False,
                "error": str(e),
                "location": {"type": "Point", "coordinates": [0.0, 0.0]},
                "confidence": 0.0
            }
    
    def _normalize_location_string(self, location: str) -> str:
        """Normalize location string for consistent caching"""
        return location.lower().strip().replace('  ', ' ')
    
    def _geocode_with_provider(self, location: str, provider: str) -> Dict:
        """Geocode with specific provider"""
        if provider == 'opencage':
            return self._geocode_opencage(location)
        elif provider == 'mapbox':
            return self._geocode_mapbox(location)
        elif provider == 'google':
            return self._geocode_google(location)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _geocode_opencage(self, location: str) -> Dict:
        """Geocode using OpenCage API"""
        url = "https://api.opencagedata.com/geocode/v1/json"
        params = {
            'q': location,
            'key': self.api_keys['opencage'],
            'limit': 1,
            'no_annotations': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['results']:
            result = data['results'][0]
            coords = result['geometry']
            
            return {
                "success": True,
                "location": {
                    "type": "Point",
                    "coordinates": [coords['lng'], coords['lat']]
                },
                "confidence": result.get('confidence', 50) / 100.0,
                "country": result['components'].get('country', ''),
                "provider": "opencage",
                "from_cache": False
            }
        else:
            return {"success": False, "error": "No results found"}
    
    def _geocode_mapbox(self, location: str) -> Dict:
        """Geocode using Mapbox API"""
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location}.json"
        params = {
            'access_token': self.api_keys['mapbox'],
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['features']:
            feature = data['features'][0]
            coords = feature['geometry']['coordinates']
            
            return {
                "success": True,
                "location": {
                    "type": "Point",
                    "coordinates": coords
                },
                "confidence": feature.get('relevance', 0.5),
                "country": self._extract_country_from_context(feature.get('context', [])),
                "provider": "mapbox",
                "from_cache": False
            }
        else:
            return {"success": False, "error": "No results found"}
    
    def _geocode_google(self, location: str) -> Dict:
        """Geocode using Google Maps API"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': location,
            'key': self.api_keys['google']
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            coords = result['geometry']['location']
            
            return {
                "success": True,
                "location": {
                    "type": "Point",
                    "coordinates": [coords['lng'], coords['lat']]
                },
                "confidence": 0.8,  # Google doesn't provide confidence scores
                "country": self._extract_country_from_google_components(
                    result.get('address_components', [])
                ),
                "provider": "google",
                "from_cache": False
            }
        else:
            return {"success": False, "error": data.get('status', 'Unknown error')}
    
    def _extract_country_from_context(self, context: List[Dict]) -> str:
        """Extract country from Mapbox context"""
        for item in context:
            if 'country' in item.get('id', ''):
                return item.get('text', '')
        return ''
    
    def _extract_country_from_google_components(self, components: List[Dict]) -> str:
        """Extract country from Google address components"""
        for component in components:
            if 'country' in component.get('types', []):
                return component.get('long_name', '')
        return ''
    
    def _cache_geocoding_result(self, original_location: str, normalized_location: str, 
                              result: Dict, provider: str):
        """Cache successful geocoding result"""
        try:
            cache_data = {
                "location_string_original": original_location,
                "location_string_normalized": normalized_location,
                "coordinates": result['location'],
                "country": result.get('country', ''),
                "confidence": result['confidence'],
                "hit_count": 1,
                "geocoding_service": provider,
                "response_metadata": {
                    "provider": provider,
                    "geocoded_at": datetime.now().isoformat()
                }
            }
            
            self.geocoding_cache.create(cache_data)
            logger.info(f"Cached geocoding result for: {original_location}")
            
        except Exception as e:
            logger.warning(f"Failed to cache geocoding result: {e}")


class EnhancedDataCollector:
    """Production-ready data collector with full database integration"""
    
    def __init__(self):
        self.service_name = "enhanced_data_collector"
        self.worker_id = f"enhanced_collector_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.data_source = DataSource()
        self.raw_data = RawProtestData()
        self.protest = Protest()
        self.processing_queue = ProcessingQueue()
        self.processing_results = ProcessingResults()
        self.data_lineage = DataLineage()
        self.validation_rules = ValidationRules()
        self.geocoding_cache = GeocodingCache()
        self.category_mapping = CategoryMapping()
        self.api_rate_limit = ApiRateLimit()
        self.service_health = ServiceHealth()
        self.collection_metrics = CollectionMetrics()
        self.error_log = ErrorLog()
        self.worker_status = WorkerStatus()
        self.service_config = ServiceConfig()
        
        # Initialize services
        self.geocoding_service = GeocodingService()
        
        from services.guardian_service import GuardianAPIService, LocationBasedProtestDetector
        from services.news_service import LocationBasedNewsAPIService  
        from services.scraper_service import PrecisionNewsRSSScraper
        
        self.guardian_service = None
        self.news_service = None
        self.scraper_service = None
        self.protest_detector = LocationBasedProtestDetector()
        
        # Collection status
        self.is_collecting = False
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # Initialize everything
        self.load_config()
        self.initialize_services()
        self.setup_validation_rules()
        self.register_worker()
    
    def setup_validation_rules(self):
        """Setup default validation rules if they don't exist"""
        try:
            existing_rules = self.validation_rules.get_active_rules()
            if not existing_rules:
                self.validation_rules.create_default_rules()
                logger.info("Created default validation rules")
        except Exception as e:
            logger.error(f"Failed to setup validation rules: {e}")
    
    def load_config(self):
        """Load configuration from database"""
        try:
            configs = self.service_config.get_service_configs(self.service_name)
            self.collection_interval_hours = configs.get('collection_interval_hours', 6)
            self.max_concurrent_sources = configs.get('max_concurrent_sources', 3)
            self.processing_batch_size = configs.get('processing_batch_size', 50)
            self.auto_collection_enabled = configs.get('auto_collection_enabled', True)
            self.geocoding_enabled = configs.get('geocoding_enabled', True)
            self.validation_enabled = configs.get('validation_enabled', True)
            
            logger.info(f"Enhanced data collector configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Use sensible defaults
            self.collection_interval_hours = 6
            self.max_concurrent_sources = 3
            self.processing_batch_size = 50
            self.auto_collection_enabled = True
            self.geocoding_enabled = True
            self.validation_enabled = True
    
    def initialize_services(self):
        """Initialize all data collection services"""
        try:
            guardian_api_key = os.getenv('GUARDIAN_API_KEY')
            if guardian_api_key:
                from services.guardian_service import GuardianAPIService
                self.guardian_service = GuardianAPIService(api_key=guardian_api_key)
                logger.info("Guardian service initialized")
            
            news_api_key = os.getenv('NEWSAPI_KEY')
            if news_api_key:
                from services.news_service import LocationBasedNewsAPIService
                self.news_service = LocationBasedNewsAPIService(api_key=news_api_key)
                logger.info("NewsAPI service initialized")
            
            from services.scraper_service import PrecisionNewsRSSScraper
            self.scraper_service = PrecisionNewsRSSScraper()
            logger.info("Scraper service initialized")
            
            logger.info("All enhanced data collection services initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            self.error_log.log_error(
                service_name=self.service_name,
                error_type="initialization_error",
                error_message=str(e),
                severity="high"
            )
    
    def register_worker(self):
        """Register this collector as a worker"""
        try:
            self.worker_status.register_worker(
                worker_id=self.worker_id,
                worker_type="enhanced_data_collector",
                host_info={
                    "service": self.service_name,
                    "capabilities": ["collection", "processing", "validation", "geocoding"]
                },
                process_id=os.getpid()
            )
            logger.info(f"Registered enhanced worker: {self.worker_id}")
        except Exception as e:
            logger.error(f"Failed to register worker: {e}")
    
    def check_api_rate_limits(self, source_name: str) -> Dict:
        """Check API rate limits before making requests"""
        try:
            return self.api_rate_limit.check_rate_limit(
                source_id=source_name,
                endpoint="main_api"
            )
        except Exception as e:
            logger.warning(f"Rate limit check failed for {source_name}: {e}")
            return {"allowed": True, "remaining": 1000}  # Default to allowed
    
    def record_api_usage(self, source_name: str, requests_made: int = 1):
        """Record API usage for rate limiting"""
        try:
            self.api_rate_limit.record_api_call(
                source_id=source_name,
                endpoint="main_api",
                requests_made=requests_made
            )
        except Exception as e:
            logger.warning(f"Failed to record API usage for {source_name}: {e}")
    
    def collect_and_store_with_full_lineage(self, source_name: str, source_config: Dict) -> Dict:
        """Enhanced collection with complete data lineage tracking"""
        logger.info(f"Starting enhanced collection from {source_name} with full lineage")
        start_time = datetime.now()
        
        try:
            # 1. Check API rate limits
            rate_limit_status = self.check_api_rate_limits(source_name)
            if not rate_limit_status.get('allowed', True):
                return {
                    "success": False,
                    "error": f"Rate limit exceeded for {source_name}. Reset at: {rate_limit_status.get('reset_time')}"
                }
            
            # 2. Collect data from source
            if source_name == "guardian" and self.guardian_service:
                result = self.guardian_service.fetch_located_protests(days_back=1, require_location=True)
            elif source_name == "newsapi" and self.news_service:
                result = self.news_service.fetch_located_protests(days_back=1, require_location=True)
            elif source_name == "scraper" and self.scraper_service:
                result = self.scraper_service.scrape_located_protests(max_workers=2)
            else:
                return {"success": False, "error": f"Unknown or unavailable source: {source_name}"}
            
            if not result.get('success', False):
                return result
            
            # 3. Record API usage
            self.record_api_usage(source_name, 1)
            
            # 4. Store with complete lineage tracking
            articles = result.get('articles', [])
            stored_count = 0
            duplicate_count = 0
            lineage_records = []
            
            for article in articles:
                try:
                    # Generate content hash for deduplication
                    content_str = f"{article.get('title', '')}{article.get('url', '')}"
                    content_hash = hashlib.md5(content_str.encode()).hexdigest()
                    
                    # Check for duplicates in raw data
                    if not self.raw_data.check_duplicate(content_hash):
                        # Store raw data with enhanced metadata
                        raw_data = {
                            "source_id": source_config.get('source_id', source_name),
                            "raw_content": article,
                            "duplicate_hash": content_hash,
                            "extraction_confidence": article.get('location_analysis', {}).get('confidence_score', 0.5),
                            "priority_level": self._calculate_priority(article),
                            "metadata": {
                                "source_name": source_name,
                                "collection_timestamp": datetime.now().isoformat(),
                                "locations_found": article.get('location_analysis', {}).get('locations_found', []),
                                "api_rate_limit_remaining": rate_limit_status.get('remaining', 0),
                                "worker_id": self.worker_id
                            }
                        }
                        
                        raw_id = self.raw_data.create(raw_data)
                        
                        # Create complete lineage record
                        lineage_data = {
                            "source_id": source_config.get('source_id', source_name),
                            "raw_data_id": raw_id,
                            "transformation_steps": [
                                {
                                    "step": "raw_collection",
                                    "timestamp": datetime.now(),
                                    "confidence_score": article.get('location_analysis', {}).get('confidence_score', 0.5),
                                    "metadata": {
                                        "collection_method": "api_fetch",
                                        "rate_limit_status": rate_limit_status,
                                        "worker_id": self.worker_id,
                                        "source_url": article.get('url', ''),
                                        "original_title": article.get('title', '')
                                    }
                                }
                            ],
                            "data_quality_flags": [],
                            "processing_notes": [
                                f"Collected from {source_name} at {datetime.now().isoformat()}"
                            ]
                        }
                        
                        lineage_id = self.data_lineage.create(lineage_data)
                        
                        # Add to processing queue
                        queue_data = {
                            "raw_data_id": raw_id,
                            "processing_type": "protest_extraction",
                            "priority": self._calculate_queue_priority(article),
                            "status": "pending",
                            "retry_count": 0,
                            "metadata": {
                                "source_confidence": article.get('location_analysis', {}).get('confidence_score', 0.5),
                                "lineage_id": lineage_id,
                                "source_name": source_name,
                                "estimated_processing_time": self._estimate_processing_time(article)
                            }
                        }
                        
                        queue_id = self.processing_queue.create(queue_data)
                        
                        stored_count += 1
                        lineage_records.append({
                            "raw_id": raw_id,
                            "lineage_id": lineage_id,
                            "queue_id": queue_id
                        })
                        
                        logger.info(f"Stored with lineage: {source_name} - {article.get('title', 'No title')[:50]}...")
                    else:
                        duplicate_count += 1
                        
                except Exception as e:
                    logger.error(f"Error storing article with lineage: {e}")
                    self.error_log.log_error(
                        service_name=self.service_name,
                        error_type="article_storage_error",
                        error_message=str(e),
                        context={
                            "source": source_name,
                            "article_url": article.get('url', ''),
                            "article_title": article.get('title', '')[:100]
                        }
                    )
                    continue
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Record comprehensive metrics
            self.collection_metrics.record_metric(
                source_id=source_config.get('source_id', source_name),
                metric_name="collection_time_seconds",
                value=processing_time,
                metric_type="gauge"
            )
            
            self.collection_metrics.record_metric(
                source_id=source_config.get('source_id', source_name),
                metric_name="articles_stored",
                value=stored_count,
                metric_type="counter"
            )
            
            self.collection_metrics.record_metric(
                source_id=source_config.get('source_id', source_name),
                metric_name="duplicates_skipped",
                value=duplicate_count,
                metric_type="counter"
            )
            
            logger.info(f"✅ Enhanced {source_name}: {stored_count} stored, {duplicate_count} duplicates, {len(lineage_records)} lineage records")
            
            return {
                "success": True,
                "source": source_name,
                "articles_collected": len(articles),
                "articles_stored": stored_count,
                "duplicates_skipped": duplicate_count,
                "lineage_records_created": len(lineage_records),
                "queued_for_processing": len(lineage_records),
                "processing_time_seconds": processing_time,
                "rate_limit_remaining": rate_limit_status.get('remaining', 0)
            }
            
        except Exception as e:
            error_msg = f"Enhanced collection failed for {source_name}: {str(e)}"
            logger.error(error_msg)
            
            self.error_log.log_error(
                service_name=self.service_name,
                error_type="enhanced_collection_error",
                error_message=error_msg,
                context={"source": source_name, "worker_id": self.worker_id},
                severity="high"
            )
            
            return {"success": False, "error": error_msg}
    
    def _calculate_priority(self, article: Dict) -> str:
        """Calculate processing priority based on article characteristics"""
        confidence = article.get('location_analysis', {}).get('confidence_score', 0.5)
        keywords = article.get('location_analysis', {}).get('protest_keywords', [])
        
        if confidence > 0.8 and len(keywords) > 2:
            return "high"
        elif confidence > 0.6:
            return "normal"
        else:
            return "low"
    
    def _calculate_queue_priority(self, article: Dict) -> int:
        """Calculate numeric priority for queue (higher = more important)"""
        priority_map = {"high": 10, "normal": 5, "low": 1}
        return priority_map.get(self._calculate_priority(article), 5)
    
    def _estimate_processing_time(self, article: Dict) -> int:
        """Estimate processing time in seconds"""
        base_time = 30  # 30 seconds base
        
        # Add time for geocoding if needed
        if not article.get('location_analysis', {}).get('coordinates'):
            base_time += 10
        
        # Add time for complex validation
        if len(article.get('title', '')) > 200:
            base_time += 5
        
        return base_time
    
    def process_queue_with_validation_pipeline(self, batch_size: int = None) -> Dict:
        """Process queue items with comprehensive validation pipeline"""
        batch_size = batch_size or self.processing_batch_size
        
        logger.info(f"Processing queue with enhanced validation pipeline (batch: {batch_size})")
        
        try:
            # Get items from processing queue
            queue_items = self.processing_queue.get_pending_items(
                processing_type="protest_extraction",
                limit=batch_size
            )
            
            if not queue_items:
                return {"success": True, "processed": 0, "message": "No queued items to process"}
            
            processed_count = 0
            validation_failures = 0
            geocoding_failures = 0
            protests_created = 0
            protests_merged = 0
            
            for queue_item in queue_items:
                try:
                    # Mark as processing
                    self.processing_queue.update_status(
                        queue_item['_id'],
                        "processing",
                        assigned_worker=self.worker_id,
                        processing_metadata={
                            "started_at": datetime.now().isoformat(),
                            "worker_capabilities": ["validation", "geocoding", "deduplication"]
                        }
                    )
                    
                    # Get raw data and lineage
                    raw_data = self.raw_data.get_by_id(queue_item['raw_data_id'])
                    lineage_id = queue_item.get('metadata', {}).get('lineage_id')
                    
                    if not raw_data:
                        self.processing_queue.update_status(
                            queue_item['_id'],
                            "failed_permanent",
                            result_data={"reason": "Raw data not found"}
                        )
                        continue
                    
                    # Extract protest data from raw content
                    protest_data = self._extract_protest_from_raw(raw_data)
                    
                    if not protest_data:
                        self.processing_queue.update_status(
                            queue_item['_id'],
                            "failed_permanent",
                            result_data={"reason": "No protest data could be extracted"}
                        )
                        continue
                    
                    # Add lineage step
                    if lineage_id:
                        self.data_lineage.add_transformation_step(lineage_id, {
                            "step": "protest_extraction",
                            "confidence_score": protest_data.get('data_quality_score', 0.5),
                            "metadata": {
                                "extraction_method": "enhanced_pipeline",
                                "worker_id": self.worker_id
                            }
                        })
                    
                    # VALIDATION PIPELINE
                    if self.validation_enabled:
                        validation_result = self._run_validation_pipeline(protest_data)
                        
                        if not validation_result['valid']:
                            validation_failures += 1
                            
                            # Store validation results
                            self.processing_results.create({
                                "raw_data_id": queue_item['raw_data_id'],
                                "validation_status": "failed",
                                "validation_errors": validation_result['errors'],
                                "validation_warnings": validation_result.get('warnings', []),
                                "confidence_score": validation_result.get('confidence', 0),
                                "needs_review": True,
                                "processing_metadata": {
                                    "worker_id": self.worker_id,
                                    "validation_rules_applied": validation_result.get('rules_applied', []),
                                    "processing_time_ms": validation_result.get('processing_time_ms', 0)
                                }
                            })
                            
                            # Add quality flag to lineage
                            if lineage_id:
                                self.data_lineage.add_quality_flag(lineage_id, {
                                    "flag_type": "validation_failed",
                                    "severity": "high",
                                    "details": validation_result['errors']
                                })
                            
                            self.processing_queue.update_status(
                                queue_item['_id'],
                                "validation_failed",
                                result_data=validation_result
                            )
                            continue
                    
                    # GEOCODING PIPELINE
                    if self.geocoding_enabled and not self._has_valid_coordinates(protest_data):
                        geocoding_result = self.geocoding_service.geocode_location(
                            protest_data['location_description']
                        )
                        
                        if geocoding_result['success']:
                            protest_data['location'] = geocoding_result['location']
                            protest_data['geocoding_confidence'] = geocoding_result['confidence']
                            protest_data['geocoding_provider'] = geocoding_result.get('provider', 'unknown')
                            
                            # Add geocoding step to lineage
                            if lineage_id:
                                self.data_lineage.add_transformation_step(lineage_id, {
                                    "step": "geocoding",
                                    "confidence_score": geocoding_result['confidence'],
                                    "metadata": {
                                        "provider": geocoding_result.get('provider'),
                                        "from_cache": geocoding_result.get('from_cache', False),
                                        "coordinates": geocoding_result['location']['coordinates']
                                    }
                                })
                        else:
                            geocoding_failures += 1
                            protest_data['needs_manual_geocoding'] = True
                            protest_data['geocoding_error'] = geocoding_result.get('error', 'Unknown error')
                            
                            # Add quality flag for geocoding failure
                            if lineage_id:
                                self.data_lineage.add_quality_flag(lineage_id, {
                                    "flag_type": "geocoding_failed",
                                    "severity": "medium",
                                    "details": {"error": geocoding_result.get('error')}
                                })
                    
                    # DEDUPLICATION AND STORAGE
                    storage_result = self._store_with_enhanced_deduplication(protest_data)
                    
                    if storage_result['action'] == 'created':
                        protests_created += 1
                        final_protest_id = storage_result['protest_id']
                    elif storage_result['action'] == 'merged':
                        protests_merged += 1
                        final_protest_id = storage_result['protest_id']
                    else:
                        # Storage failed
                        self.processing_queue.update_status(
                            queue_item['_id'],
                            "failed_permanent",
                            result_data={"reason": "Storage failed", "error": storage_result.get('error')}
                        )
                        continue
                    
                    # Update lineage with final protest ID
                    if lineage_id:
                        self.data_lineage.update_final_protest_id(lineage_id, final_protest_id)
                        self.data_lineage.add_transformation_step(lineage_id, {
                            "step": "final_storage",
                            "confidence_score": protest_data.get('data_quality_score', 0.5),
                            "metadata": {
                                "final_protest_id": str(final_protest_id),
                                "storage_action": storage_result['action'],
                                "worker_id": self.worker_id
                            }
                        })
                    
                    # Store successful processing results
                    self.processing_results.create({
                        "raw_data_id": queue_item['raw_data_id'],
                        "validation_status": "passed",
                        "confidence_score": protest_data.get('data_quality_score', 0.5),
                        "final_protest_id": final_protest_id,
                        "processing_metadata": {
                            "worker_id": self.worker_id,
                            "storage_action": storage_result['action'],
                            "geocoding_success": geocoding_result.get('success', False) if self.geocoding_enabled else None,
                            "validation_warnings": validation_result.get('warnings', []) if self.validation_enabled else [],
                            "processing_completed_at": datetime.now().isoformat()
                        }
                    })
                    
                    # Mark queue item as completed
                    self.processing_queue.update_status(
                        queue_item['_id'],
                        "completed",
                        result_data={
                            "final_protest_id": str(final_protest_id),
                            "storage_action": storage_result['action'],
                            "processing_summary": {
                                "validation_passed": True,
                                "geocoding_success": geocoding_result.get('success', False) if self.geocoding_enabled else None,
                                "quality_score": protest_data.get('data_quality_score', 0.5)
                            }
                        }
                    )
                    
                    processed_count += 1
                    logger.info(f"Enhanced processing completed: {storage_result['action']} protest {final_protest_id}")
                    
                except Exception as e:
                    # Handle individual processing errors with enhanced error tracking
                    error_context = {
                        "queue_item_id": str(queue_item['_id']),
                        "raw_data_id": str(queue_item['raw_data_id']),
                        "lineage_id": str(queue_item.get('metadata', {}).get('lineage_id', '')),
                        "worker_id": self.worker_id,
                        "processing_step": "unknown"
                    }
                    
                    self.error_log.log_error(
                        service_name=self.service_name,
                        error_type="item_processing_error",
                        error_message=str(e),
                        context=error_context,
                        severity="medium"
                    )
                    
                    # Implement retry logic
                    retry_count = queue_item.get('retry_count', 0) + 1
                    max_retries = 3
                    
                    if retry_count <= max_retries:
                        # Schedule for retry
                        self.processing_queue.update_status(
                            queue_item['_id'],
                            "failed_retry",
                            retry_count=retry_count,
                            result_data={
                                "error": str(e),
                                "retry_scheduled_for": (datetime.now() + timedelta(minutes=retry_count * 5)).isoformat()
                            }
                        )
                        logger.warning(f"Scheduled retry {retry_count}/{max_retries} for queue item {queue_item['_id']}")
                    else:
                        # Permanent failure
                        self.processing_queue.update_status(
                            queue_item['_id'],
                            "failed_permanent",
                            result_data={
                                "error": str(e),
                                "max_retries_reached": True,
                                "failed_permanently_at": datetime.now().isoformat()
                            }
                        )
                        logger.error(f"Permanent failure for queue item {queue_item['_id']} after {max_retries} retries")
            
            # Calculate success metrics
            total_items = len(queue_items)
            success_rate = processed_count / total_items if total_items > 0 else 0
            
            # Record processing metrics
            self.collection_metrics.record_metric(
                source_id="processing_pipeline",
                metric_name="processing_success_rate",
                value=success_rate,
                metric_type="gauge"
            )
            
            self.collection_metrics.record_metric(
                source_id="processing_pipeline",
                metric_name="validation_failure_rate",
                value=validation_failures / total_items if total_items > 0 else 0,
                metric_type="gauge"
            )
            
            logger.info(f"Enhanced processing completed: {processed_count}/{total_items} items, "
                       f"{protests_created} created, {protests_merged} merged, "
                       f"{validation_failures} validation failures")
            
            return {
                "success": True,
                "total_items": total_items,
                "processed": processed_count,
                "protests_created": protests_created,
                "protests_merged": protests_merged,
                "validation_failures": validation_failures,
                "geocoding_failures": geocoding_failures,
                "success_rate": success_rate,
                "failed": total_items - processed_count
            }
            
        except Exception as e:
            error_msg = f"Enhanced processing pipeline failed: {str(e)}"
            logger.error(error_msg)
            
            self.error_log.log_error(
                service_name=self.service_name,
                error_type="processing_pipeline_error",
                error_message=error_msg,
                severity="high"
            )
            
            return {"success": False, "error": error_msg}
    
    def _extract_protest_from_raw(self, raw_data: Dict) -> Optional[Dict]:
        """Extract protest data from raw content with enhanced processing"""
        try:
            raw_content = raw_data.get('raw_content', {})
            source_id = raw_data.get('source_id', '')
            
            # Determine processing method based on source
            if 'guardian' in source_id:
                return self._process_guardian_content(raw_content)
            elif 'newsapi' in source_id:
                return self._process_newsapi_content(raw_content)
            elif 'scraper' in source_id:
                return self._process_scraper_content(raw_content)
            else:
                logger.warning(f"Unknown source type in raw data: {source_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting protest from raw data: {e}")
            return None
    
    def _process_guardian_content(self, raw_content: Dict) -> Optional[Dict]:
        """Process Guardian content into structured protest data"""
        try:
            location_analysis = raw_content.get('location_analysis', {})
            
            if not location_analysis.get('is_protest') or not location_analysis.get('locations_found'):
                return None
            
            title = raw_content.get('title', '')
            url = raw_content.get('url', '')
            published_at = raw_content.get('publishedAt', '')
            
            # Parse date with better error handling
            start_date = self._parse_date_safely(published_at)
            
            # Enhanced category mapping
            categories = self._map_keywords_to_categories_enhanced(
                location_analysis.get('protest_keywords', []),
                title,
                raw_content.get('standfirst', '')
            )
            
            return {
                'title': title,
                'description': raw_content.get('standfirst', '') or raw_content.get('trailText', ''),
                'location': {"type": "Point", "coordinates": [0.0, 0.0]},  # Will be geocoded
                'location_description': ', '.join(location_analysis['locations_found']),
                'start_date': start_date,
                'categories': categories,
                'organizers': self._extract_organizers(raw_content),
                'data_sources': ['guardian'],
                'external_links': [url],
                'verification_status': 'verified',
                'data_quality_score': self._calculate_quality_score(raw_content, 'guardian'),
                'source_metadata': {
                    'guardian_section': raw_content.get('section', ''),
                    'confidence_score': location_analysis.get('confidence_score', 0),
                    'protest_type': location_analysis.get('protest_type', 'unknown'),
                    'publication_date': published_at,
                    'byline': raw_content.get('byline', ''),
                    'word_count': len(raw_content.get('standfirst', '').split())
                },
                'content_hash': self._generate_content_hash(title, location_analysis['locations_found'], published_at)
            }
            
        except Exception as e:
            logger.error(f"Error processing Guardian content: {e}")
            return None
    
    def _process_newsapi_content(self, raw_content: Dict) -> Optional[Dict]:
        """Process NewsAPI content into structured protest data"""
        try:
            location_analysis = raw_content.get('location_analysis', {})
            
            if not location_analysis.get('is_protest') or not location_analysis.get('locations_found'):
                return None
            
            title = raw_content.get('title', '')
            url = raw_content.get('url', '')
            published_at = raw_content.get('publishedAt', '')
            
            start_date = self._parse_date_safely(published_at)
            
            categories = self._map_keywords_to_categories_enhanced(
                location_analysis.get('protest_keywords', []),
                title,
                raw_content.get('description', '')
            )
            
            return {
                'title': title,
                'description': raw_content.get('description', ''),
                'location': {"type": "Point", "coordinates": [0.0, 0.0]},
                'location_description': ', '.join(location_analysis['locations_found']),
                'start_date': start_date,
                'categories': categories,
                'organizers': self._extract_organizers(raw_content),
                'data_sources': ['newsapi'],
                'external_links': [url],
                'verification_status': 'auto_verified',
                'data_quality_score': self._calculate_quality_score(raw_content, 'newsapi'),
                'source_metadata': {
                    'news_source': raw_content.get('source', {}).get('name', ''),
                    'confidence_score': location_analysis.get('confidence_score', 0),
                    'protest_type': location_analysis.get('protest_type', 'unknown'),
                    'publication_date': published_at,
                    'author': raw_content.get('author', ''),
                    'source_url': raw_content.get('source', {}).get('url', '')
                },
                'content_hash': self._generate_content_hash(title, location_analysis['locations_found'], published_at)
            }
            
        except Exception as e:
            logger.error(f"Error processing NewsAPI content: {e}")
            return None
    
    def _process_scraper_content(self, raw_content: Dict) -> Optional[Dict]:
        """Process scraper content into structured protest data"""
        try:
            location_analysis = raw_content.get('location_analysis', {})
            
            if not location_analysis.get('is_protest') or not location_analysis.get('locations_found'):
                return None
            
            title = raw_content.get('title', '')
            url = raw_content.get('url', '')
            published_at = raw_content.get('publishedAt', '')
            
            start_date = self._parse_date_safely(published_at)
            
            categories = self._map_keywords_to_categories_enhanced(
                location_analysis.get('protest_keywords', []),
                title,
                raw_content.get('description', '')
            )
            
            return {
                'title': title,
                'description': raw_content.get('description', ''),
                'location': {"type": "Point", "coordinates": [0.0, 0.0]},
                'location_description': ', '.join(location_analysis['locations_found']),
                'start_date': start_date,
                'categories': categories,
                'organizers': self._extract_organizers(raw_content),
                'data_sources': ['rss_scraper'],
                'external_links': [url],
                'verification_status': 'pending',
                'data_quality_score': self._calculate_quality_score(raw_content, 'scraper'),
                'source_metadata': {
                    'feed_source': raw_content.get('source', ''),
                    'confidence_score': location_analysis.get('confidence_score', 0),
                    'protest_type': location_analysis.get('protest_type', 'unknown'),
                    'publication_date': published_at,
                    'feed_url': raw_content.get('feed_url', ''),
                    'scraping_timestamp': raw_content.get('scraping_timestamp', '')
                },
                'content_hash': self._generate_content_hash(title, location_analysis['locations_found'], published_at)
            }
            
        except Exception as e:
            logger.error(f"Error processing scraper content: {e}")
            return None
    
    def _parse_date_safely(self, date_string: str) -> datetime:
        """Safely parse date string with multiple format support"""
        if not date_string:
            return datetime.now()
        
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string.replace('Z', ''), fmt.replace('Z', ''))
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_string}")
        return datetime.now()
    
    def _map_keywords_to_categories_enhanced(self, keywords: List[str], title: str, description: str) -> List[str]:
        """Enhanced category mapping with context analysis"""
        if not keywords and not title:
            return ['Other']
        
        try:
            # Combine all text for analysis
            full_text = f"{title} {description} {' '.join(keywords)}".lower()
            
            # Get category mappings from database
            mappings = self.category_mapping.get_active_mappings()
            
            categories = set()
            category_scores = {}
            
            for mapping in mappings:
                score = 0
                mapping_keywords = mapping.get('keywords', [])
                
                for keyword in mapping_keywords:
                    if keyword.lower() in full_text:
                        score += mapping.get('confidence_weight', 1.0)
                
                if score > 0:
                    category = mapping.get('category', 'Other')
                    categories.add(category)
                    category_scores[category] = category_scores.get(category, 0) + score
            
            # Return top categories sorted by score
            if categories:
                sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
                return [cat for cat, score in sorted_categories[:3]]  # Top 3 categories
            else:
                return ['Other']
                
        except Exception as e:
            logger.warning(f"Enhanced category mapping failed: {e}")
            return ['Other']
    
    def _extract_organizers(self, raw_content: Dict) -> List[str]:
        """Extract organizer information from content"""
        organizers = []
        
        # Look for common organizer patterns
        text_fields = [
            raw_content.get('description', ''),
            raw_content.get('standfirst', ''),
            raw_content.get('title', '')
        ]
        
        organizer_patterns = [
            r'organized by ([^,.]+)',
            r'([^,.]+) organized',
            r'([^,.]+) union',
            r'([^,.]+) coalition',
            r'([^,.]+) movement'
        ]
        
        import re
        
        for text in text_fields:
            if not text:
                continue
                
            for pattern in organizer_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    organizer = match.strip()
                    if len(organizer) > 3 and organizer not in organizers:
                        organizers.append(organizer)
        
        return organizers[:5]  # Limit to 5 organizers
    
    def _calculate_quality_score(self, raw_content: Dict, source_type: str) -> float:
        """Calculate data quality score based on content characteristics"""
        score = 0.5  # Base score
        
        # Source reliability bonus
        source_bonus = {
            'guardian': 0.3,
            'newsapi': 0.2,
            'scraper': 0.1
        }
        score += source_bonus.get(source_type, 0)
        
        # Content quality factors
        title = raw_content.get('title', '')
        description = raw_content.get('description', '') or raw_content.get('standfirst', '')
        
        if len(title) > 20:
            score += 0.1
        if len(description) > 50:
            score += 0.1
        
        # Location analysis quality
        location_analysis = raw_content.get('location_analysis', {})
        confidence = location_analysis.get('confidence_score', 0)
        score += confidence * 0.2
        
        # URL validity
        if raw_content.get('url', '').startswith('https://'):
            score += 0.05
        
        # Publication recency
        published_at = raw_content.get('publishedAt', '')
        if published_at:
            try:
                pub_date = self._parse_date_safely(published_at)
                days_old = (datetime.now() - pub_date).days
                if days_old <= 7:
                    score += 0.1
                elif days_old <= 30:
                    score += 0.05
            except:
                pass
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _generate_content_hash(self, title: str, locations: List[str], date_str: str) -> str:
        """Generate content hash for deduplication"""
        normalized_title = title.lower().strip()
        normalized_locations = sorted([loc.lower().strip() for loc in locations])
        normalized_date = date_str[:10] if date_str else ""
        
        content_string = f"{normalized_title}|{','.join(normalized_locations)}|{normalized_date}"
        return hashlib.md5(content_string.encode()).hexdigest()
    
    def _run_validation_pipeline(self, protest_data: Dict) -> Dict:
        """Run comprehensive validation pipeline with database rules"""
        try:
            start_time = time.time()
            
            # Get active validation rules
            validation_rules = self.validation_rules.get_active_rules()
            
            errors = []
            warnings = []
            confidence_score = 1.0
            rules_applied = []
            
            for rule in validation_rules:
                try:
                    rule_result = self._apply_validation_rule(protest_data, rule)
                    rules_applied.append(rule['rule_name'])
                    
                    if rule_result['failed']:
                        if rule['severity'] == 'critical':
                            errors.append({
                                "rule": rule['rule_name'],
                                "message": rule_result['message'],
                                "field": rule['field_name'],
                                "severity": "critical"
                            })
                            confidence_score *= 0.5  # Severe penalty
                        else:
                            warnings.append({
                                "rule": rule['rule_name'],
                                "message": rule_result['message'],
                                "field": rule['field_name'],
                                "severity": "warning"
                            })
                            confidence_score *= 0.9  # Minor penalty
                            
                except Exception as e:
                    logger.warning(f"Validation rule {rule.get('rule_name', 'unknown')} failed: {e}")
                    continue
            
            # Check overall data quality thresholds
            min_confidence = 0.4  # Lower threshold for more lenient validation
            valid = len(errors) == 0 and confidence_score >= min_confidence
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "valid": valid,
                "confidence": confidence_score,
                "errors": errors,
                "warnings": warnings,
                "rules_applied": rules_applied,
                "processing_time_ms": processing_time_ms,
                "validation_summary": {
                    "critical_errors": len([e for e in errors if e.get('severity') == 'critical']),
                    "warnings": len(warnings),
                    "rules_checked": len(rules_applied)
                }
            }
            
        except Exception as e:
            logger.error(f"Validation pipeline error: {e}")
            return {
                "valid": False,
                "confidence": 0.0,
                "errors": [{"rule": "validation_system", "message": str(e), "severity": "critical"}],
                "warnings": [],
                "rules_applied": []
            }
    
    def _apply_validation_rule(self, protest_data: Dict, rule: Dict) -> Dict:
        """Apply individual validation rule"""
        try:
            field_name = rule['field_name']
            validation_type = rule['validation_type']
            config = rule.get('validation_config', {})
            
            # Get field value (support nested fields like 'location.coordinates')
            field_value = self._get_nested_field_value(protest_data, field_name)
            
            if validation_type == 'required':
                if field_value is None or field_value == '':
                    return {"failed": True, "message": rule['error_message']}
                    
            elif validation_type == 'length':
                if field_value and isinstance(field_value, str):
                    length = len(field_value)
                    min_len = config.get('min_length', 0)
                    max_len = config.get('max_length', float('inf'))
                    
                    if length < min_len or length > max_len:
                        return {"failed": True, "message": rule['error_message']}
                        
            elif validation_type == 'coordinates':
                if field_value and isinstance(field_value, list) and len(field_value) == 2:
                    lat, lng = field_value
                    allow_zero = config.get('allow_zero', True)
                    
                    if not allow_zero and lat == 0.0 and lng == 0.0:
                        return {"failed": True, "message": rule['error_message']}
                    
                    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                        return {"failed": True, "message": "Invalid coordinate range"}
                        
            elif validation_type == 'date_range':
                if field_value and isinstance(field_value, datetime):
                    min_date_str = config.get('min_date')
                    max_date_str = config.get('max_date')
                    
                    if min_date_str:
                        min_date = datetime.fromisoformat(min_date_str.replace('Z', ''))
                        if field_value < min_date:
                            return {"failed": True, "message": rule['error_message']}
                    
                    if max_date_str:
                        max_date = datetime.fromisoformat(max_date_str.replace('Z', ''))
                        if field_value > max_date:
                            return {"failed": True, "message": rule['error_message']}
                            
            elif validation_type == 'text_quality':
                if field_value and isinstance(field_value, str):
                    words = field_value.split()
                    min_words = config.get('min_words', 1)
                    max_repetition = config.get('max_repetition', 1.0)
                    
                    if len(words) < min_words:
                        return {"failed": True, "message": rule['error_message']}
                    
                    # Check for excessive repetition
                    if len(words) > 5:
                        unique_words = set(words)
                        repetition_ratio = len(unique_words) / len(words)
                        if repetition_ratio < (1 - max_repetition):
                            return {"failed": True, "message": "Excessive word repetition detected"}
            
            return {"failed": False, "message": "Validation passed"}
            
        except Exception as e:
            return {"failed": True, "message": f"Validation rule error: {str(e)}"}
    
    def _get_nested_field_value(self, data: Dict, field_path: str):
        """Get value from nested field path (e.g., 'location.coordinates')"""
        try:
            fields = field_path.split('.')
            value = data
            
            for field in fields:
                if isinstance(value, dict) and field in value:
                    value = value[field]
                else:
                    return None
                    
            return value
        except:
            return None
    
    def _has_valid_coordinates(self, protest_data: Dict) -> bool:
        """Check if protest has valid coordinates"""
        location = protest_data.get('location', {})
        coords = location.get('coordinates', [])
        
        if not isinstance(coords, list) or len(coords) != 2:
            return False
        
        lat, lng = coords
        return not (lat == 0.0 and lng == 0.0)
    
    def _store_with_enhanced_deduplication(self, protest_data: Dict) -> Dict:
        """Store protest with enhanced deduplication logic"""
        try:
            content_hash = protest_data.get('content_hash')
            
            # Check for exact hash match
            existing_by_hash = self.protest.find_one({"content_hash": content_hash})
            
            if existing_by_hash:
                # Merge data
                merge_result = self._merge_protest_data(existing_by_hash, protest_data)
                self.protest.update_by_id(existing_by_hash['_id'], merge_result)
                
                return {
                    "action": "merged",
                    "protest_id": existing_by_hash['_id'],
                    "merge_data": merge_result
                }
            
            # Check for similarity-based matches
            similar_protest = self._find_similar_protest(protest_data)
            
            if similar_protest:
                # Merge with similar protest
                merge_result = self._merge_protest_data(similar_protest, protest_data)
                self.protest.update_by_id(similar_protest['_id'], merge_result)
                
                return {
                    "action": "merged",
                    "protest_id": similar_protest['_id'],
                    "merge_data": merge_result
                }
            
            # Create new protest
            protest_data.update({
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'visibility': 'public',
                'status': 'active',
                'trending_score': 0.0,
                'featured': False,
                'engagement_metrics': {
                    'views': 0,
                    'shares': 0,
                    'bookmarks': 0
                },
                'merge_count': 0
            })
            
            protest_id = self.protest.create(protest_data)
            
            return {
                "action": "created",
                "protest_id": protest_id
            }
            
        except Exception as e:
            return {
                "action": "failed",
                "error": str(e)
            }
    
    def _find_similar_protest(self, protest_data: Dict) -> Optional[Dict]:
        """Find similar protests using advanced similarity detection"""
        try:
            title = protest_data['title']
            location_desc = protest_data['location_description']
            start_date = protest_data['start_date']
            
            # Search within 7 days and same general location
            date_start = start_date - timedelta(days=7)
            date_end = start_date + timedelta(days=7)
            
            # Get location keywords for matching
            location_words = set(location_desc.lower().split())
            main_location = location_desc.split(',')[0].strip() if ',' in location_desc else location_desc
            
            # Search for potentially similar protests
            potential_matches = list(self.protest.find_many({
                "start_date": {"$gte": date_start, "$lte": date_end},
                "visibility": "public"
            }, limit=20))
            
            # Calculate similarity scores
            for protest in potential_matches:
                similarity_score = self._calculate_similarity_score(protest_data, protest)
                if similarity_score >= 0.7:  # 70% similarity threshold
                    return protest
            
            return None
            
        except Exception as e:
            logger.warning(f"Similarity search failed: {e}")
            return None
    
    def _calculate_similarity_score(self, new_protest: Dict, existing_protest: Dict) -> float:
        """Calculate similarity score between two protests"""
        try:
            score = 0.0
            
            # Title similarity (40% weight)
            title_sim = self._text_similarity(
                new_protest.get('title', ''),
                existing_protest.get('title', '')
            )
            score += title_sim * 0.4
            
            # Location similarity (30% weight)
            location_sim = self._text_similarity(
                new_protest.get('location_description', ''),
                existing_protest.get('location_description', '')
            )
            score += location_sim * 0.3
            
            # Date proximity (20% weight)
            date_sim = self._date_similarity(
                new_protest.get('start_date'),
                existing_protest.get('start_date')
            )
            score += date_sim * 0.2
            
            # Category overlap (10% weight)
            category_sim = self._category_similarity(
                new_protest.get('categories', []),
                existing_protest.get('categories', [])
            )
            score += category_sim * 0.1
            
            return score
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard index"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _date_similarity(self, date1: datetime, date2: datetime) -> float:
        """Calculate date similarity (closer dates = higher score)"""
        if not date1 or not date2:
            return 0.0
        
        days_diff = abs((date1 - date2).days)
        
        if days_diff == 0:
            return 1.0
        elif days_diff <= 3:
            return 0.8
        elif days_diff <= 7:
            return 0.5
        else:
            return 0.0
    
    def _category_similarity(self, categories1: List[str], categories2: List[str]) -> float:
        """Calculate category overlap similarity"""
        if not categories1 or not categories2:
            return 0.0
        
        set1 = set(categories1)
        set2 = set(categories2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _merge_protest_data(self, existing: Dict, new_data: Dict) -> Dict:
        """Merge new protest data into existing protest"""
        try:
            # Combine data sources
            existing_sources = set(existing.get('data_sources', []))
            new_sources = set(new_data.get('data_sources', []))
            combined_sources = list(existing_sources.union(new_sources))
            
            # Combine external links
            existing_links = existing.get('external_links', [])
            new_links = new_data.get('external_links', [])
            combined_links = list(set(existing_links + new_links))
            
            # Take higher quality score
            existing_quality = existing.get('data_quality_score', 0)
            new_quality = new_data.get('data_quality_score', 0)
            
            # Merge verification status (take highest priority)
            verification_priority = {
                'verified': 4,
                'auto_verified': 3,
                'pending': 2,
                'unverified': 1
            }
            
            existing_status = existing.get('verification_status', 'unverified')
            new_status = new_data.get('verification_status', 'unverified')
            
            best_status = max(
                existing_status, new_status,
                key=lambda x: verification_priority.get(x, 0)
            )
            
            # Combine categories
            existing_categories = existing.get('categories', [])
            new_categories = new_data.get('categories', [])
            combined_categories = list(set(existing_categories + new_categories))
            
            # Combine organizers
            existing_organizers = existing.get('organizers', [])
            new_organizers = new_data.get('organizers', [])
            combined_organizers = list(set(existing_organizers + new_organizers))
            
            # Update coordinates if new data has better geocoding
            location_update = {}
            if new_data.get('geocoding_confidence', 0) > existing.get('geocoding_confidence', 0):
                location_update = {
                    'location': new_data.get('location', existing.get('location')),
                    'geocoding_confidence': new_data.get('geocoding_confidence', 0),
                    'geocoding_provider': new_data.get('geocoding_provider', '')
                }
            
            # Merge source metadata
            existing_metadata = existing.get('source_metadata', {})
            new_metadata = new_data.get('source_metadata', {})
            combined_metadata = {**existing_metadata, **new_metadata}
            
            merge_data = {
                'data_sources': combined_sources,
                'external_links': combined_links,
                'data_quality_score': max(existing_quality, new_quality),
                'verification_status': best_status,
                'categories': combined_categories,
                'organizers': combined_organizers,
                'source_metadata': combined_metadata,
                'updated_at': datetime.now(),
                'merge_count': existing.get('merge_count', 0) + 1,
                'last_merged_at': datetime.now().isoformat(),
                'merge_history': existing.get('merge_history', []) + [{
                    'merged_at': datetime.now().isoformat(),
                    'merged_from': new_data.get('data_sources', []),
                    'quality_improvement': new_quality - existing_quality
                }]
            }
            
            # Add location updates if applicable
            merge_data.update(location_update)
            
            return merge_data
            
        except Exception as e:
            logger.error(f"Error merging protest data: {e}")
            return {"updated_at": datetime.now()}
    
    def run_complete_enhanced_collection_cycle(self) -> Dict:
        """Run complete enhanced collection cycle with all features"""
        if self.is_collecting:
            return {"success": False, "error": "Collection already in progress"}
        
        logger.info("🚀 Starting COMPLETE ENHANCED collection cycle")
        start_time = datetime.now()
        
        try:
            self.is_collecting = True
            
            # Update worker status
            self.worker_status.update_heartbeat(
                self.worker_id,
                status="collecting",
                current_task="enhanced_collection_cycle"
            )
            
            # 1. ENHANCED HEALTH CHECK
            logger.info(" Running enhanced health checks...")
            health_results = self._run_enhanced_health_checks()
            
            # 2. COLLECTION WITH FULL LINEAGE
            logger.info(" Enhanced collection with full lineage tracking...")
            sources = {
                "guardian": {"source_id": "guardian_001", "enabled": True},
                "newsapi": {"source_id": "newsapi_001", "enabled": True},
                "scraper": {"source_id": "scraper_001", "enabled": True}
            }
            
            collection_results = {}
            
            with ThreadPoolExecutor(max_workers=self.max_concurrent_sources) as executor:
                future_to_source = {
                    executor.submit(self.collect_and_store_with_full_lineage, source_name, config): source_name
                    for source_name, config in sources.items()
                    if config.get('enabled', False)
                }
                
                for future in as_completed(future_to_source):
                    source_name = future_to_source[future]
                    try:
                        result = future.result()
                        collection_results[source_name] = result
                        logger.info(f" {source_name}: {result.get('articles_stored', 0)} articles stored")
                    except Exception as e:
                        logger.error(f" Collection failed for {source_name}: {e}")
                        collection_results[source_name] = {"success": False, "error": str(e)}
            
            # 3. ENHANCED PROCESSING WITH VALIDATION
            logger.info(" Enhanced processing with validation pipeline...")
            processing_result = self.process_queue_with_validation_pipeline()
            
            # 4. QUEUE STATISTICS
            queue_stats = self.processing_queue.get_statistics()
            
            collection_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate comprehensive totals
            total_stored = sum(
                result.get('articles_stored', 0)
                for result in collection_results.values()
                if result.get('success', False)
            )
            
            total_lineage_records = sum(
                result.get('lineage_records_created', 0)
                for result in collection_results.values()
                if result.get('success', False)
            )
            
            successful_sources = sum(1 for result in collection_results.values() if result.get('success', False))
            
            # Record comprehensive health status
            overall_status = "healthy" if successful_sources > 0 and processing_result.get('success', False) else "degraded"
            
            self.service_health.record_health_check(
                service_name=self.service_name,
                status=overall_status,
                response_time_ms=int(collection_time * 1000),
                check_type="complete_collection_cycle",
                metrics={
                    "total_articles_stored": total_stored,
                    "total_lineage_records": total_lineage_records,
                    "successful_sources": successful_sources,
                    "protests_created": processing_result.get('protests_created', 0),
                    "protests_merged": processing_result.get('protests_merged', 0),
                    "validation_failures": processing_result.get('validation_failures', 0),
                    "geocoding_failures": processing_result.get('geocoding_failures', 0),
                    "collection_time_seconds": collection_time,
                    "queue_pending": queue_stats.get('pending', 0),
                    "queue_processing": queue_stats.get('processing', 0),
                    "queue_completed": queue_stats.get('completed', 0),
                    "processing_success_rate": processing_result.get('success_rate', 0)
                }
            )
            
            # Update worker status
            self.worker_status.update_heartbeat(
                self.worker_id,
                status="idle",
                current_task="collection_completed",
                last_collection_stats={
                    "articles_stored": total_stored,
                    "protests_processed": processing_result.get('processed', 0),
                    "success_rate": processing_result.get('success_rate', 0)
                }
            )
            
            logger.info(f" ENHANCED collection cycle completed:")
            logger.info(f"    {total_stored} articles stored from {successful_sources} sources")
            logger.info(f"    {total_lineage_records} lineage records created")
            logger.info(f"     {processing_result.get('protests_created', 0)} new protests created")
            logger.info(f"    {processing_result.get('protests_merged', 0)} protests merged")
            logger.info(f"     {processing_result.get('validation_failures', 0)} validation failures")
            logger.info(f"    {processing_result.get('geocoding_failures', 0)} geocoding failures")
            logger.info(f"     Completed in {collection_time:.2f} seconds")
            
            return {
                "success": True,
                "collection_time_seconds": round(collection_time, 2),
                "sources_collected": successful_sources,
                "total_articles_stored": total_stored,
                "total_lineage_records": total_lineage_records,
                "protests_created": processing_result.get('protests_created', 0),
                "protests_merged": processing_result.get('protests_merged', 0),
                "validation_failures": processing_result.get('validation_failures', 0),
                "geocoding_failures": processing_result.get('geocoding_failures', 0),
                "processing_success_rate": processing_result.get('success_rate', 0),
                "queue_statistics": queue_stats,
                "health_status": overall_status,
                "source_results": collection_results,
                "processing_result": processing_result,
                "health_checks": health_results
            }
            
        except Exception as e:
            error_msg = f"Enhanced collection cycle failed: {str(e)}"
            logger.error(error_msg)
            
            self.error_log.log_error(
                service_name=self.service_name,
                error_type="enhanced_collection_cycle_error",
                error_message=error_msg,
                severity="critical"
            )
            
            # Update worker status to error
            self.worker_status.update_heartbeat(
                self.worker_id,
                status="error",
                current_task="collection_failed",
                error_message=error_msg
            )
            
            return {"success": False, "error": error_msg}
            
        finally:
            self.is_collecting = False
    
    def _run_enhanced_health_checks(self) -> List[Dict]:
        """Run comprehensive health checks on all services"""
        try:
            health_results = []
            
            services_to_check = [
                {"name": "guardian_api", "service": self.guardian_service},
                {"name": "newsapi", "service": self.news_service},
                {"name": "scraper_service", "service": self.scraper_service},
                {"name": "geocoding_service", "service": self.geocoding_service},
                {"name": "database_connection", "service": None}
            ]
            
            for service_info in services_to_check:
                start_time = datetime.now()
                service_name = service_info['name']
                
                try:
                    if service_name == "database_connection":
                        # Test database connectivity
                        health_check = self._test_database_connectivity()
                    elif service_name == "geocoding_service":
                        # Test geocoding service
                        health_check = self._test_geocoding_service()
                    else:
                        # Test API services
                        health_check = self._test_api_service(service_info['service'])
                    
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Record detailed health status
                    self.service_health.record_health_check(
                        service_name=service_name,
                        status="healthy" if health_check.get('healthy', False) else "unhealthy",
                        response_time_ms=response_time,
                        check_type="enhanced_health_check",
                        metrics=health_check.get('metrics', {}),
                        error_message=health_check.get('error')
                    )
                    
                    health_results.append({
                        "service": service_name,
                        "healthy": health_check.get('healthy', False),
                        "response_time_ms": response_time,
                        "details": health_check
                    })
                    
                except Exception as e:
                    # Record health check failure
                    self.service_health.record_health_check(
                        service_name=service_name,
                        status="error",
                        response_time_ms=5000,
                        check_type="enhanced_health_check",
                        error_message=str(e)
                    )
                    
                    health_results.append({
                        "service": service_name,
                        "healthy": False,
                        "error": str(e)
                    })
            
            return health_results
            
        except Exception as e:
            logger.error(f"Enhanced health check failed: {e}")
            return []
    
    def _test_database_connectivity(self) -> Dict:
        """Test database connectivity and basic operations"""
        try:
            # Test basic database operations
            test_count = self.protest.count()
            queue_count = self.processing_queue.get_statistics()
            
            return {
                "healthy": True,
                "metrics": {
                    "total_protests": test_count,
                    "queue_pending": queue_count.get('pending', 0),
                    "database_responsive": True
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "metrics": {"database_responsive": False}
            }
    
    def _test_geocoding_service(self) -> Dict:
        """Test geocoding service functionality"""
        try:
            # Test with a simple location
            test_result = self.geocoding_service.geocode_location("New York, NY")
            
            return {
                "healthy": test_result.get('success', False),
                "metrics": {
                    "geocoding_responsive": test_result.get('success', False),
                    "from_cache": test_result.get('from_cache', False),
                    "provider": test_result.get('provider', 'unknown')
                },
                "error": test_result.get('error') if not test_result.get('success') else None
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "metrics": {"geocoding_responsive": False}
            }
    
    def _test_api_service(self, service) -> Dict:
        """Test API service health"""
        try:
            if service is None:
                return {"healthy": False, "error": "Service not initialized"}
            
            return {
                "healthy": True,
                "metrics": {
                    "service_initialized": True,
                    "api_key_configured": hasattr(service, 'api_key') and bool(service.api_key)
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "metrics": {"service_initialized": False}
            }
    
    def get_comprehensive_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            # Basic status
            basic_status = {
                "service": self.service_name,
                "worker_id": self.worker_id,
                "is_collecting": self.is_collecting,
                "scheduler_running": self.scheduler_running,
                "configuration": {
                    "collection_interval_hours": self.collection_interval_hours,
                    "processing_batch_size": self.processing_batch_size,
                    "geocoding_enabled": self.geocoding_enabled,
                    "validation_enabled": self.validation_enabled
                }
            }
            
            # Enhanced metrics
            health_status = self.service_health.get_service_status(self.service_name)
            queue_stats = self.processing_queue.get_statistics()
            processing_stats = self.raw_data.get_processing_statistics()
            
            # Database statistics
            db_stats = {
                "total_protests": self.protest.count(),
                "total_raw_data": self.raw_data.count(),
                "total_lineage_records": self.data_lineage.collection.count_documents({}),
                "active_validation_rules": len(self.validation_rules.get_active_rules()),
                "geocoding_cache_size": self.geocoding_cache.collection.count_documents({})
            }
            
            # Recent metrics (24 hours)
            recent_metrics = self.collection_metrics.get_metrics_summary(hours=24)
            
            # Service availability
            services_status = {
                "guardian": self.guardian_service is not None,
                "newsapi": self.news_service is not None,
                "scraper": self.scraper_service is not None,
                "geocoding": True,  # Always available
                "validation": self.validation_enabled
            }
            
            return {
                **basic_status,
                "health_status": health_status.get("status", "unknown"),
                "last_health_check": health_status.get("last_check"),
                "queue_statistics": queue_stats,
                "processing_statistics": processing_stats,
                "database_statistics": db_stats,
                "recent_metrics_24h": recent_metrics,
                "services_status": services_status,
                "performance": {
                    "avg_collection_time": recent_metrics.get('avg_collection_time_seconds', 0),
                    "success_rate": recent_metrics.get('success_rate', 0),
                    "articles_per_hour": recent_metrics.get('articles_per_hour', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            return {
                "service": self.service_name,
                "status": "error",
                "error": str(e)
            }
    
    def start_enhanced_scheduler(self):
        """Start enhanced scheduler with better error handling"""
        if self.scheduler_running:
            logger.info("Enhanced scheduler already running")
            return
        
        def run_enhanced_scheduler():
            schedule.every(self.collection_interval_hours).hours.do(
                self.run_complete_enhanced_collection_cycle
            )
            
            # Health check every 15 minutes
            schedule.every(15).minutes.do(self._run_enhanced_health_checks)
            
            self.scheduler_running = True
            logger.info(f" Enhanced scheduler started - collection every {self.collection_interval_hours} hours")
            
            while self.scheduler_running:
                try:
                    schedule.run_pending()
                    
                    # Update worker heartbeat
                    self.worker_status.update_heartbeat(
                        self.worker_id,
                        status="scheduler_running",
                        current_task="waiting_for_next_cycle"
                    )
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    self.error_log.log_error(
                        service_name=self.service_name,
                        error_type="scheduler_error",
                        error_message=str(e),
                        severity="medium"
                    )
                    time.sleep(60)  # Continue despite errors
        
        self.scheduler_thread = threading.Thread(target=run_enhanced_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_enhanced_scheduler(self):
        """Stop enhanced scheduler gracefully"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        # Update worker status
        self.worker_status.shutdown_worker(
            self.worker_id,
            reason="scheduler_stopped"
        )
        
        logger.info("Enhanced scheduler stopped")


# Global enhanced instance
enhanced_data_collector_instance = None

def get_enhanced_data_collector():
    """Get or create enhanced data collector instance"""
    global enhanced_data_collector_instance
    if enhanced_data_collector_instance is None:
        enhanced_data_collector_instance = EnhancedDataCollector()
    return enhanced_data_collector_instance

def initialize_enhanced_data_collector():
    """Initialize enhanced data collector and start scheduler"""
    collector = get_enhanced_data_collector()
    if collector.auto_collection_enabled:
        collector.start_enhanced_scheduler()
        logger.info(" Enhanced data collector initialized with automatic scheduling")
    return collector

def shutdown_enhanced_data_collector():
    """Shutdown enhanced data collector gracefully"""
    global enhanced_data_collector_instance
    if enhanced_data_collector_instance:
        enhanced_data_collector_instance.stop_enhanced_scheduler()
        logger.info(" Enhanced data collector shutdown completed")


# Testing and development
if __name__ == '__main__':
    print(" Testing ENHANCED Data Collector - COMPLETE DATABASE INTEGRATION")
    print("=" * 80)
    
    try:
        print(" Initializing enhanced data collector...")
        collector = EnhancedDataCollector()
        print(" Enhanced collector initialized with ALL database features")
        
        print("\n Getting comprehensive status...")
        status = collector.get_comprehensive_status()
        print(f" Status: {status['health_status']}")
        print(f"   Database: {status['database_statistics']['total_protests']} protests")
        print(f"   Queue: {status['queue_statistics']['pending']} pending")
        print(f"   Services: {sum(status['services_status'].values())}/{len(status['services_status'])} available")
        
        print("\n Testing complete enhanced collection cycle...")
        print("  This will store real data with full lineage tracking!")
        
        confirm = input("Run complete enhanced cycle? (y/N): ")
        if confirm.lower() == 'y':
            print(" Running COMPLETE enhanced collection cycle...")
            result = collector.run_complete_enhanced_collection_cycle()
            
            if result['success']:
                print(f" ENHANCED collection successful!")
                print(f"    Articles stored: {result['total_articles_stored']}")
                print(f"    Lineage records: {result['total_lineage_records']}")
                print(f"     New protests: {result['protests_created']}")
                print(f"    Merged protests: {result['protests_merged']}")
                print(f"     Validation failures: {result['validation_failures']}")
                print(f"    Geocoding failures: {result['geocoding_failures']}")
                print(f"    Success rate: {result['processing_success_rate']:.1%}")
                print(f"     Time: {result['collection_time_seconds']}s")
                print(f"    Health: {result['health_status']}")
            else:
                print(f" Enhanced collection failed: {result['error']}")
        else:
            print("  Skipped enhanced collection test")
        
        print("\n Enhanced data collector testing completed!")
        print("\n COMPLETE INTEGRATION FEATURES:")
        print("    Full database schema utilization (35 collections)")
        print("    Complete data lineage tracking")
        print("    Comprehensive validation pipeline")
        print("    Real geocoding with caching")
        print("    API rate limit management")
        print("    Enhanced deduplication")
        print("    Worker coordination")
        print("    Comprehensive error handling")
        print("    Advanced health monitoring")
        print("    Processing queue management")
        print("    Data quality scoring")
        print("    Retry mechanisms")
        print("    Performance metrics")
        
    except Exception as e:
        print(f" Enhanced test failed: {e}")
        import traceback
        print("\n Full error trace:")
        print(traceback.format_exc())