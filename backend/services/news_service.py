import re
import requests
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urlencode
import time
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LocationProtestMatch:
    """Data class for location-based protest detection"""
    is_protest: bool
    confidence_score: float
    locations_found: List[str]
    protest_keywords: List[str]
    protest_type: str
    participant_count: Optional[str]
    reason: str

class LocationBasedProtestDetector:
    """Location-focused protest detection - much more reliable"""
    
    def __init__(self):
        # Simple core protest words
        self.core_protest_words = {
            'protest', 'demonstration', 'march', 'rally', 'strike', 
            'boycott', 'uprising', 'riot', 'picket', 'walkout',
            'sit-in', 'blockade', 'civil disobedience'
        }
        
        # Additional protest context words
        self.protest_context = {
            'protesters', 'demonstrators', 'activists', 'marchers',
            'strikers', 'crowd', 'gathering', 'assembly'
        }
        
        # Improved location patterns
        self.location_patterns = [
            # City, State patterns (most reliable)
            r'\bin\s+([A-Z][a-zA-Z\s]{2,20}?),\s*([A-Z][A-Z])\b',  # "in Seattle, WA"
            r'\bin\s+([A-Z][a-zA-Z\s]{2,20}?),\s*([A-Z][a-zA-Z\s]{3,15})\b',  # "in Seattle, Washington"
            
            # Simple "in [City]" patterns (limited length to avoid long phrases)
            r'\bin\s+(downtown\s+)?([A-Z][a-zA-Z]{3,15})\b(?!\s+(?:over|about|during|where|as|after|when|with|and|or))',  # "in Seattle" but not "in Seattle over"
            r'\bin\s+([A-Z][a-zA-Z\s]{4,20}?)\s+(?:as|where|during|after)\b',  # "in New York as"
            
            # "at [Place] in [City]" patterns
            r'\bat\s+[A-Z][a-zA-Z\s]+?\s+in\s+([A-Z][a-zA-Z\s]{3,15})\b',  # "at Ford plant in Detroit"
            r'\bat\s+[A-Z][a-zA-Z\s]+?\s+([A-Z][a-zA-Z\s]{3,15})\s+(?:campus|university|college)\b',  # "at University California campus"
            
            # Institution patterns
            r'\b(?:at|outside|near)\s+([A-Z][a-zA-Z\s]+?\s+(?:University|College))\b',  # "at Harvard University"
            r'\b(?:at|outside|near)\s+(City Hall|Parliament|Capitol|Federal Building)\b',  # Known buildings
            
            # Street/landmark patterns (shorter to avoid long phrases)
            r'\b(?:at|on|near)\s+([A-Z][a-zA-Z\s]{5,25}?\s+(?:Street|Avenue|Boulevard|Square|Plaza|Park))\b',
            
            # International city patterns
            r'\bin\s+([A-Z][a-zA-Z\s]{3,15}?),?\s*(?:UK|France|Germany|Canada|Australia|India|Brazil|Mexico|England|Scotland)\b',
            
            # US State patterns
            r'\bin\s+([A-Z][a-zA-Z\s]{4,20}?),?\s+(?:California|Texas|Florida|New York|Pennsylvania|Illinois|Ohio|Georgia|Michigan|Virginia|Washington|Arizona|Massachusetts|Tennessee|Maryland|Colorado|Minnesota|Wisconsin|Oregon|Nevada|Indiana|North Carolina|South Carolina|Alabama|Louisiana|Kentucky|Arkansas|Iowa|Kansas|Utah|Oklahoma|Mississippi|Nebraska|West Virginia|Idaho|Hawaii|Maine|New Hampshire|Vermont|Delaware|Rhode Island|Montana|North Dakota|South Dakota|Wyoming|Alaska)\b'
        ]
        
        # Known cities/places (you can expand this)
        self.known_locations = {
            # Major US cities
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
            'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
            'San Francisco', 'Columbus', 'Fort Worth', 'Indianapolis', 'Charlotte',
            'Seattle', 'Denver', 'Washington', 'Boston', 'Nashville', 'Baltimore',
            'Portland', 'Las Vegas', 'Detroit', 'Memphis', 'Louisville', 'Milwaukee',
            'Atlanta', 'Miami', 'Oakland', 'Minneapolis', 'Cleveland', 'Kansas City',
            
            # International cities
            'London', 'Paris', 'Berlin', 'Tokyo', 'Sydney', 'Toronto', 'Vancouver',
            'Mexico City', 'Buenos Aires', 'São Paulo', 'Mumbai', 'Delhi', 'Beijing',
            'Shanghai', 'Seoul', 'Bangkok', 'Singapore', 'Hong Kong', 'Dubai',
            'Cairo', 'Lagos', 'Nairobi', 'Cape Town', 'Istanbul', 'Moscow',
            
            # US States (for broader matching)
            'California', 'Texas', 'Florida', 'New York', 'Pennsylvania', 'Illinois',
            'Ohio', 'Georgia', 'North Carolina', 'Michigan', 'New Jersey', 'Virginia',
            'Washington', 'Arizona', 'Massachusetts', 'Tennessee', 'Indiana', 'Maryland',
            'Missouri', 'Wisconsin', 'Colorado', 'Minnesota', 'South Carolina', 'Alabama',
            
            # Common place names
            'downtown', 'city center', 'capitol', 'university', 'campus', 'city hall',
            'federal building', 'state house', 'courthouse', 'police station'
        }
        
        # Number patterns for crowd size
        self.crowd_patterns = [
            r'(\d+(?:,\d+)*)\s*(?:people|protesters|demonstrators|marchers|strikers)',
            r'(?:thousands|hundreds|dozens)\s+of\s+(?:people|protesters|demonstrators)',
            r'crowd\s+of\s+(\d+(?:,\d+)*)',
            r'(?:about|approximately|nearly|over)\s+(\d+(?:,\d+)*)\s*(?:people|protesters)'
        ]
    
    def extract_locations(self, text: str) -> List[str]:
        """Extract locations using improved patterns"""
        locations = set()
        
        # Apply location patterns with better processing
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle multi-group matches - take the main city/location
                    for part in match:
                        part_clean = part.strip()
                        if part_clean and len(part_clean) <= 20:
                            locations.add(part_clean)
                else:
                    match_clean = match.strip()
                    if len(match_clean) <= 20:
                        locations.add(match_clean)
        
        # Additional simple patterns for common cases
        simple_patterns = [
            r'\bin\s+(downtown\s+)?([A-Z][a-zA-Z]{3,12})\b',  # "in Seattle", "in downtown Seattle"
            r'\bin\s+([A-Z][a-zA-Z]{3,12})\s+(?:area|region|city)\b',  # "in Seattle area"
        ]
        
        for pattern in simple_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    for part in match:
                        if part and part.strip() not in ['downtown', 'area', 'region', 'city']:
                            locations.add(part.strip())
                else:
                    locations.add(match.strip())
        
        # Clean and validate locations
        valid_locations = []
        for loc in locations:
            loc_clean = loc.strip()
            
            # Skip if too short, too long, or contains problematic words
            if (len(loc_clean) < 3 or len(loc_clean) > 20 or
                any(word in loc_clean.lower() for word in ['over', 'about', 'during', 'where', 'when', 'with', 'and', 'or', 'the', 'arrest', 'police', 'protesters'])):
                continue
            
            # Check if it's a known location or looks like a proper place name
            if (loc_clean in self.known_locations or 
                (loc_clean[0].isupper() and 
                 all(c.isalpha() or c.isspace() for c in loc_clean) and
                 not loc_clean.lower() in ['protest', 'demonstration', 'march', 'rally', 'strike'])):
                valid_locations.append(loc_clean)
        
        # Remove duplicates and return top 3 (most specific)
        unique_locations = list(set(valid_locations))
        
        # Sort by specificity (known locations first, then by length)
        unique_locations.sort(key=lambda x: (x not in self.known_locations, len(x)))
        
        return unique_locations[:3]
    
    def extract_crowd_size(self, text: str) -> Optional[str]:
        """Extract crowd size information"""
        for pattern in self.crowd_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0] if isinstance(matches[0], str) else str(matches[0])
        return None
    
    def has_protest_keywords(self, text: str) -> Tuple[List[str], str]:
        """Check for protest keywords and determine type"""
        text_lower = text.lower()
        found_keywords = []
        protest_type = "unknown"
        
        # Check core protest words
        for word in self.core_protest_words:
            if word in text_lower:
                found_keywords.append(word)
                
                # Determine type
                if word in ['strike', 'walkout']:
                    protest_type = "labor_action"
                elif word in ['riot', 'uprising']:
                    protest_type = "unrest"
                elif word in ['march', 'demonstration', 'protest', 'rally']:
                    protest_type = "peaceful_protest"
        
        # Check context words
        for word in self.protest_context:
            if word in text_lower:
                found_keywords.append(word)
        
        return found_keywords, protest_type
    
    def analyze_article(self, article: Dict) -> LocationProtestMatch:
        """Analyze article with location-first approach"""
        # Extract text content
        title = article.get('title', '') or ''
        description = article.get('description', '') or ''
        content = article.get('content', '') or ''
        
        full_text = f"{title} {description} {content}"
        
        # Step 1: Extract locations
        locations = self.extract_locations(full_text)
        
        # Step 2: Check for protest keywords
        protest_keywords, protest_type = self.has_protest_keywords(full_text)
        
        # Step 3: Extract crowd size
        crowd_size = self.extract_crowd_size(full_text)
        
        # Step 4: Calculate confidence
        confidence = 0.0
        reason = ""
        
        if not locations:
            # No location = very low confidence
            confidence = 0.0
            reason = "No specific location found"
            is_protest = False
            
        elif not protest_keywords:
            # Location but no protest words = not a protest
            confidence = 0.0
            reason = f"Location found ({', '.join(locations[:2])}) but no protest keywords"
            is_protest = False
            
        else:
            # Both location AND protest keywords = high confidence
            base_confidence = 0.7
            
            # Boost for multiple locations
            if len(locations) > 1:
                base_confidence += 0.1
            
            # Boost for multiple protest keywords
            base_confidence += min(len(protest_keywords) * 0.05, 0.2)
            
            # Boost for crowd size information
            if crowd_size:
                base_confidence += 0.1
            
            # Boost for title mentions
            title_lower = title.lower()
            if any(keyword in title_lower for keyword in protest_keywords):
                base_confidence += 0.1
            
            confidence = min(base_confidence, 1.0)
            
            is_protest = confidence >= 0.6
            
            if is_protest:
                reason = f"Location + protest keywords found: {locations[0]} + {', '.join(protest_keywords[:3])}"
            else:
                reason = f"Low confidence despite location: only {len(protest_keywords)} protest indicators"
        
        return LocationProtestMatch(
            is_protest=is_protest,
            confidence_score=round(confidence, 3),
            locations_found=locations,
            protest_keywords=protest_keywords,
            protest_type=protest_type,
            participant_count=crowd_size,
            reason=reason
        )
    
    def filter_protest_articles(self, articles: List[Dict], require_location: bool = True) -> List[Tuple[Dict, LocationProtestMatch]]:
        """Filter articles requiring specific locations"""
        protest_articles = []
        
        for article in articles:
            analysis = self.analyze_article(article)
            
            # Strict requirements: must have location AND be classified as protest
            if require_location:
                if analysis.locations_found and analysis.is_protest:
                    protest_articles.append((article, analysis))
            else:
                # Relaxed requirements
                if analysis.is_protest:
                    protest_articles.append((article, analysis))
        
        # Sort by confidence, then by number of locations
        protest_articles.sort(key=lambda x: (x[1].confidence_score, len(x[1].locations_found)), reverse=True)
        
        return protest_articles


class LocationBasedNewsAPIService:
    """NewsAPI service with location-based protest detection"""
    
    def __init__(self, api_key: str = None):
        self.source_id = "newsapi_location"
        self.base_url = "https://newsapi.org/v2"
        self.service_name = "location_newsapi_service"
        self.min_request_interval = 1
        self.last_request_time = None
        
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')
        if not self.api_key:
            logger.warning("No NewsAPI key provided")
        
        # Initialize location-based detector
        self.protest_detector = LocationBasedProtestDetector()
        
        # Configuration
        self.request_timeout = 30
        self.max_articles_per_request = 100
    
    def wait_for_rate_limit(self):
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)
    
    def record_request(self):
        self.last_request_time = time.time()
    
    def build_location_search_params(self, days_back: int = 7, language: str = "en") -> Dict:
        """Build search parameters focused on locationable protests"""
        
        # Use terms that are likely to have locations
        location_focused_keywords = [
            "protest in", "demonstration in", "rally in", "march in",
            "strike at", "protesters in", "demonstrators in",
            "civil rights march", "climate protest", "labor strike",
            "downtown protest", "university protest", "capitol protest"
        ]
        
        # Build query
        query = " OR ".join([f'"{keyword}"' for keyword in location_focused_keywords])
        
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        return {
            'q': query,
            'language': language,
            'sortBy': 'publishedAt',
            'pageSize': self.max_articles_per_request,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'apiKey': self.api_key
        }
    
    def fetch_located_protests(self, days_back: int = 7, require_location: bool = True) -> Dict:
        """Fetch protests that have specific locations"""
        start_time = datetime.now()
        
        if not self.api_key:
            return {"success": False, "error": "No API key provided"}
        
        try:
            self.wait_for_rate_limit()
            
            # Build request with location-focused terms
            params = self.build_location_search_params(days_back)
            url = f"{self.base_url}/everything"
            
            logger.info(f"Fetching location-based protest news...")
            logger.info(f"Query: {params['q'][:100]}...")
            
            # Make request
            response = requests.get(url, params=params, timeout=self.request_timeout)
            response.raise_for_status()
            self.record_request()
            
            # Parse response
            data = response.json()
            if data.get('status') != 'ok':
                return {"success": False, "error": data.get('message', 'API error')}
            
            raw_articles = data.get('articles', [])
            total_raw = len(raw_articles)
            
            logger.info(f"Analyzing {total_raw} articles for location-based protests...")
            
            # Filter using location-based detection
            protest_articles = self.protest_detector.filter_protest_articles(
                raw_articles, 
                require_location=require_location
            )
            
            # Process results
            processed_protests = []
            for article, analysis in protest_articles:
                processed_article = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("publishedAt", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "urlToImage": article.get("urlToImage", ""),
                    
                    # Location-based analysis
                    "location_analysis": {
                        "confidence_score": analysis.confidence_score,
                        "locations_found": analysis.locations_found,
                        "protest_keywords": analysis.protest_keywords[:5],
                        "protest_type": analysis.protest_type,
                        "participant_count": analysis.participant_count,
                        "reason": analysis.reason
                    }
                }
                processed_protests.append(processed_article)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate statistics
            all_locations = []
            for _, analysis in protest_articles:
                all_locations.extend(analysis.locations_found)
            
            location_counts = {}
            for loc in all_locations:
                location_counts[loc] = location_counts.get(loc, 0) + 1
            
            protest_types = {}
            for _, analysis in protest_articles:
                protest_types[analysis.protest_type] = protest_types.get(analysis.protest_type, 0) + 1
            
            logger.info(f"Found {len(protest_articles)} located protest articles from {total_raw} total")
            
            return {
                "success": True,
                "total_articles_scanned": total_raw,
                "located_protests_found": len(protest_articles),
                "filter_efficiency": round(len(protest_articles) / total_raw * 100, 1) if total_raw > 0 else 0,
                "processing_time_seconds": round(processing_time, 2),
                "top_locations": dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
                "protest_types": protest_types,
                "articles": processed_protests[:15]  # Return top 15
            }
            
        except Exception as e:
            error_msg = f"Error in location-based protest detection: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}


