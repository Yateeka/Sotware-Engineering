import re
import requests
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin, urlparse, quote_plus
import time
import os
from dataclasses import dataclass
import feedparser
from newspaper import Article
import concurrent.futures
from threading import Lock

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
    """Highly accurate location-focused protest detection"""
    
    def __init__(self):
        # Core protest words
        self.core_protest_words = {
            'protest', 'demonstration', 'march', 'rally', 'strike', 
            'boycott', 'uprising', 'riot', 'picket', 'walkout',
            'sit-in', 'blockade', 'civil disobedience'
        }
        
        # Additional protest context words (updated)
        self.protest_context = {
            'protesters', 'demonstrators', 'activists', 'marchers',
            'strikers', 'crowd', 'gathering', 'assembly', 'clashes',
            'clash', 'tensions', 'unrest', 'violence'
        }
        
        # Comprehensive known locations (validated list)
        self.known_locations = {
            # Major US cities (verified)
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
            'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
            'San Francisco', 'Columbus', 'Fort Worth', 'Indianapolis', 'Charlotte',
            'Seattle', 'Denver', 'Washington', 'Boston', 'Nashville', 'Baltimore',
            'Portland', 'Las Vegas', 'Detroit', 'Memphis', 'Louisville', 'Milwaukee',
            'Atlanta', 'Miami', 'Oakland', 'Minneapolis', 'Cleveland', 'Kansas City',
            'Sacramento', 'Tampa', 'Orlando', 'Pittsburgh', 'Cincinnati', 'Toledo',
            'Buffalo', 'Rochester', 'Syracuse', 'Albany', 'Richmond', 'Norfolk',
            'Virginia Beach', 'Raleigh', 'Durham', 'Charleston', 'Columbia',
            
            # International cities (major ones)
            'London', 'Paris', 'Berlin', 'Tokyo', 'Sydney', 'Toronto', 'Vancouver',
            'Mexico City', 'Buenos Aires', 'São Paulo', 'Mumbai', 'Delhi', 'Beijing',
            'Shanghai', 'Seoul', 'Bangkok', 'Singapore', 'Hong Kong', 'Dubai',
            'Tel Aviv', 'Jerusalem', 'Haifa', 'Barcelona', 'Madrid', 'Rome', 'Milan',
            'Vienna', 'Prague', 'Budapest', 'Warsaw', 'Stockholm', 'Damascus', 'Aleppo',
            
            # Syrian cities (for the current article)
            'Syria', 'Suweida', 'Damascus', 'Aleppo', 'Homs', 'Latakia', 'Daraa',
            
            # US States (abbreviated and full)
            'California', 'Texas', 'Florida', 'New York', 'Pennsylvania', 'Illinois',
            'Ohio', 'Georgia', 'North Carolina', 'Michigan', 'New Jersey', 'Virginia',
            'Washington', 'Arizona', 'Massachusetts', 'Tennessee', 'Indiana', 'Maryland',
            'Missouri', 'Wisconsin', 'Colorado', 'Minnesota', 'South Carolina', 'Alabama',
            'Louisiana', 'Kentucky', 'Oregon', 'Oklahoma', 'Connecticut', 'Arkansas',
            
            # Universities and landmarks
            'UCLA', 'USC', 'Harvard', 'Stanford', 'MIT', 'Yale', 'Princeton',
            'Berkeley', 'NYU', 'Columbia', 'Georgetown', 'GWU',
            'City Hall', 'Capitol Hill', 'Capitol Building', 'White House',
            'Times Square', 'Central Park', 'Brooklyn', 'Manhattan', 'Queens',
            
            # Common place descriptors
            'downtown', 'university', 'campus'
        }
        
        # Location patterns (comprehensive but precise)
        self.location_patterns = [
            # City, State patterns (most reliable)
            r'\bin\s+([A-Z][a-zA-Z\s]{2,20}?),\s*([A-Z][A-Z])\b',  # "in Seattle, WA"
            r'\bin\s+([A-Z][a-zA-Z\s]{2,20}?),\s*([A-Z][a-zA-Z\s]{3,15})\b',  # "in Seattle, Washington"
            
            # Simple "in [City]" patterns
            r'\bin\s+(downtown\s+)?([A-Z][a-zA-Z]{3,15})\b',  # "in Seattle", "in downtown Seattle"
            r'\bat\s+[A-Z][a-zA-Z\s]+?\s+in\s+([A-Z][a-zA-Z\s]{3,15})\b',  # "at Ford plant in Detroit"
            
            # Institution patterns
            r'\b(?:at|outside|near)\s+([A-Z][a-zA-Z\s]+?\s+(?:University|College|Capitol|Hall))\b',
            
            # International patterns
            r'\bin\s+([A-Z][a-zA-Z\s]{3,15}?),\s*(?:UK|France|Germany|Canada|Australia|Israel|Japan|China|India|Brazil|Mexico)\b',
        ]
        
        # Crowd size patterns
        self.crowd_patterns = [
            r'(\d+(?:,\d+)*)\s*(?:people|protesters|demonstrators|marchers|strikers)',
            r'(?:thousands|hundreds|dozens)\s+of\s+(?:people|protesters|demonstrators)',
            r'crowd\s+of\s+(\d+(?:,\d+)*)',
            r'(?:about|approximately|nearly|over)\s+(\d+(?:,\d+)*)\s*(?:people|protesters)'
        ]
    
    def extract_locations(self, text: str) -> List[str]:
        """Extract locations using improved patterns with contextual search and multi-word support"""
        locations = set()
        
        # Apply regex patterns (keep as fallback)
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    for part in match:
                        part_clean = part.strip()
                        if part_clean and len(part_clean) >= 3 and len(part_clean) <= 15:
                            locations.add(part_clean)
                else:
                    match_clean = match.strip()
                    if len(match_clean) >= 3 and len(match_clean) <= 15:
                        locations.add(match_clean)
        
        # Enhanced approach: Find known locations with context (including multi-word)
        prepositions = ['in', 'at', 'near', 'outside', 'from', 'to']
        words = text.split()
        
        # Check for single word locations
        for i, word in enumerate(words):
            for loc in self.known_locations:
                if word.lower() == loc.lower():
                    # Check if there's a preposition within the previous 3 words
                    for j in range(max(0, i-3), i):
                        if words[j].lower() in prepositions:
                            locations.add(loc)
                            break
        
        # Check for two-word locations (like "Tel Aviv", "New York", "Los Angeles")
        for i in range(len(words) - 1):
            two_word = f"{words[i]} {words[i+1]}"
            for loc in self.known_locations:
                if two_word.lower() == loc.lower():
                    # Check if there's a preposition within the previous 3 words of the first word
                    for j in range(max(0, i-3), i):
                        if words[j].lower() in prepositions:
                            locations.add(loc)
                            break
        
        # Check for three-word locations (like "New York City")
        for i in range(len(words) - 2):
            three_word = f"{words[i]} {words[i+1]} {words[i+2]}"
            for loc in self.known_locations:
                if three_word.lower() == loc.lower():
                    # Check if there's a preposition within the previous 3 words of the first word
                    for j in range(max(0, i-3), i):
                        if words[j].lower() in prepositions:
                            locations.add(loc)
                            break
        
        # Clean and validate locations
        valid_locations = []
        # Words that indicate the preceding word is likely a person's name
        name_following_verbs = ['said', 'told', 'attended', 'protested', 'marched', 'spoke', 'declared', 'announced', 'reported', 'hoists', 'holds']
        
        for loc in locations:
            loc_clean = loc.strip()
            
            # Basic validation
            if len(loc_clean) < 3 or len(loc_clean) > 25:  # Increased max length for multi-word
                continue
            if loc_clean.lower() in ['protest', 'demonstration', 'rally', 'strike']:
                continue
                
            # Exclude if followed by name-indicating verbs
            pattern = r'\b' + re.escape(loc_clean) + r'\s+(' + '|'.join(name_following_verbs) + r')\b'
            if re.search(pattern, text, re.IGNORECASE):
                continue
                
            # Accept if in known locations or looks like proper place name
            if loc_clean in self.known_locations or (loc_clean[0].isupper() and all(c.isalpha() or c.isspace() for c in loc_clean)):
                valid_locations.append(loc_clean)
        
        # Remove duplicates and prioritize known locations
        unique_locations = list(set(valid_locations))
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
    
    def analyze_text(self, title: str, content: str) -> LocationProtestMatch:
        """Analyze text content for protest + location"""
        full_text = f"{title} {content}"
        
        # Extract locations
        locations = self.extract_locations(full_text)
        
        # Check for protest keywords
        protest_keywords, protest_type = self.has_protest_keywords(full_text)
        
        # Extract crowd size
        crowd_size = self.extract_crowd_size(full_text)
        
        # Calculate confidence
        confidence = 0.0
        reason = ""
        
        if not locations:
            confidence = 0.0
            reason = "No specific location found"
            is_protest = False
        elif not protest_keywords:
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
            
            # Boost for crowd size
            if crowd_size:
                base_confidence += 0.1
            
            # Boost for title mentions
            title_lower = title.lower()
            if any(keyword in title_lower for keyword in protest_keywords):
                base_confidence += 0.1
            
            confidence = min(base_confidence, 1.0)
            is_protest = confidence >= 0.6
            
            if is_protest:
                reason = f"Location + protest keywords: {locations[0]} + {', '.join(protest_keywords[:3])}"
            else:
                reason = f"Low confidence: only {len(protest_keywords)} protest indicators"
        
        return LocationProtestMatch(
            is_protest=is_protest,
            confidence_score=round(confidence, 3),
            locations_found=locations,
            protest_keywords=protest_keywords,
            protest_type=protest_type,
            participant_count=crowd_size,
            reason=reason
        )


class PrecisionNewsRSSScraper:
    """Precision RSS-based news scraper - fewer sources, better accuracy"""
    
    def __init__(self):
        self.protest_detector = LocationBasedProtestDetector()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.min_request_interval = 1.0
        self.last_request_time = None
        self.request_lock = Lock()
        self.request_timeout = 15
        
        # VERIFIED working RSS feeds (tested manually)
        self.rss_feeds = {
            'bbc_main': {
                'url': 'https://feeds.bbci.co.uk/news/rss.xml',
                'name': 'BBC News'
            },
            'npr_news': {
                'url': 'https://feeds.npr.org/1001/rss.xml', 
                'name': 'NPR News'
            },
            'techcrunch': {
                'url': 'https://techcrunch.com/feed/',
                'name': 'TechCrunch'  # Has some protest coverage
            }
        }
        
        # More specific protest search terms  
        self.protest_search_terms = [
            'protest', 'demonstration', 'rally', 'march', 'strike',
            'protesters', 'demonstrators', 'civil rights',
            'boycott', 'uprising', 'picket', 'walkout',
            # Add broader terms to catch more articles for testing
            'activism', 'activist', 'riot', 'clash', 'tensions',
            'clashes'  # plural form
        ]
        
        print(f"🔍 Debug: Protest search terms: {self.protest_search_terms}")
    
    def wait_for_rate_limit(self):
        """Rate limiting"""
        with self.request_lock:
            if self.last_request_time:
                time_since_last = time.time() - self.last_request_time
                if time_since_last < self.min_request_interval:
                    time.sleep(self.min_request_interval - time_since_last)
            self.last_request_time = time.time()
    
    def test_rss_feed(self, feed_url: str) -> bool:
        """Test if RSS feed is working"""
        try:
            response = self.session.get(feed_url, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                return len(feed.entries) > 0 and not feed.bozo
            return False
        except:
            return False
    
    def fetch_rss_feed(self, feed_url: str, feed_name: str) -> List[Dict]:
        """Fetch RSS feed with validation"""
        try:
            self.wait_for_rate_limit()
            
            logger.info(f"Testing RSS feed: {feed_name}")
            
            # Test feed first
            if not self.test_rss_feed(feed_url):
                logger.warning(f"RSS feed test failed for {feed_name}")
                return []
            
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"RSS parsing issues for {feed_name}: {feed.bozo_exception}")
                return []
            
            articles = []
            logger.info(f"Processing {len(feed.entries)} entries from {feed_name}")
            
            for entry in feed.entries[:15]:  # Limit to 15 per feed
                try:
                    title = entry.get('title', 'No title')
                    link = entry.get('link', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    
                    print(f"\n📄 Processing entry:")
                    print(f"   Title: {title}")
                    print(f"   Description: {description[:100]}...")
                    
                    # Parse date
                    published = ''
                    if hasattr(entry, 'published'):
                        published = entry.published
                    elif hasattr(entry, 'updated'):
                        published = entry.updated
                    
                    # Filter for protest-related content
                    full_text = f"{title} {description}".lower()
                    print(f"🔍 Checking article: {title[:50]}...")
                    print(f"   📝 Full text preview: {full_text[:100]}...")
                    
                    # Check each search term
                    found_terms = []
                    for term in self.protest_search_terms:
                        if term in full_text:
                            found_terms.append(term)
                    
                    if found_terms:
                        print(f"   ✅ MATCH! Found terms: {found_terms}")
                        article = {
                            'title': title,
                            'url': link,
                            'description': description,
                            'publishedAt': published,
                            'source': feed_name,
                            'feed_url': feed_url
                        }
                        articles.append(article)
                        logger.info(f"Found protest-related: {title[:50]}...")
                    else:
                        print(f"   ❌ No protest terms found")
                        
                except Exception as e:
                    logger.warning(f"Error processing entry from {feed_name}: {str(e)}")
                    continue
            
            logger.info(f"Found {len(articles)} protest-related articles from {feed_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_name}: {str(e)}")
            return []
    
    def extract_article_content(self, article: Dict) -> Dict:
        """Extract content with newspaper3k"""
        url = article.get('url', '')
        if not url:
            return article
        
        try:
            self.wait_for_rate_limit()
            
            news_article = Article(url)
            news_article.download()
            news_article.parse()
            
            # Add extracted content with fallback
            article['content'] = news_article.text[:3000] if news_article.text else article.get('description', '')
            article['authors'] = news_article.authors if news_article.authors else []
            article['publish_date'] = str(news_article.publish_date) if news_article.publish_date else article.get('publishedAt', '')
            
            logger.info(f"Content extracted: {url[:50]}...")
            
        except Exception as e:
            logger.warning(f"Content extraction failed for {url}: {str(e)}")
            article['content'] = article.get('description', '')
        
        return article
    
    def scrape_located_protests(self, max_workers: int = 2) -> Dict:
        """Main scraping function with precision focus"""
        start_time = datetime.now()
        
        logger.info("Starting precision RSS-based protest scraping...")
        
        # Test all feeds first
        working_feeds = {}
        for feed_id, feed_info in self.rss_feeds.items():
            if self.test_rss_feed(feed_info['url']):
                working_feeds[feed_id] = feed_info
                logger.info(f"✅ RSS feed working: {feed_info['name']}")
            else:
                logger.warning(f"❌ RSS feed failed: {feed_info['name']}")
        
        if not working_feeds:
            return {
                "success": False,
                "error": "No working RSS feeds found",
                "working_feeds": 0
            }
        
        # Collect articles from working feeds
        all_articles = []
        for feed_id, feed_info in working_feeds.items():
            articles = self.fetch_rss_feed(feed_info['url'], feed_info['name'])
            all_articles.extend(articles)
        
        logger.info(f"Collected {len(all_articles)} protest-related articles")
        
        if not all_articles:
            return {
                "success": True,
                "message": "No protest-related articles found in current feeds",
                "working_feeds": len(working_feeds),
                "total_articles_collected": 0,
                "unique_articles": 0,
                "articles_analyzed": 0,
                "located_protests_found": 0,
                "filter_efficiency": 0,
                "processing_time_seconds": round((datetime.now() - start_time).total_seconds(), 2),
                "top_locations": {},
                "protest_types": {},
                "sources": {},
                "articles": []
            }
        
        # Remove duplicates
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        logger.info(f"After deduplication: {len(unique_articles)} unique articles")
        
        # Extract content for top articles
        articles_to_process = unique_articles[:10]  # Process top 10 for speed
        articles_with_content = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.extract_article_content, article) 
                      for article in articles_to_process]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    article_with_content = future.result()
                    articles_with_content.append(article_with_content)
                except Exception as e:
                    logger.warning(f"Content extraction error: {str(e)}")
        
        logger.info(f"Extracted content for {len(articles_with_content)} articles")
        
        # Analyze for location-based protests
        protest_articles = []
        
        for article in articles_with_content:
            title = article.get('title', '')
            content = article.get('content', '') or article.get('description', '')
            
            analysis = self.protest_detector.analyze_text(title, content)
            
            # Only include if has locations AND is protest
            if analysis.locations_found and analysis.is_protest:
                article['location_analysis'] = {
                    'confidence_score': analysis.confidence_score,
                    'locations_found': analysis.locations_found,
                    'protest_keywords': analysis.protest_keywords[:5],
                    'protest_type': analysis.protest_type,
                    'participant_count': analysis.participant_count,
                    'reason': analysis.reason
                }
                protest_articles.append(article)
        
        # Sort by confidence
        protest_articles.sort(key=lambda x: x['location_analysis']['confidence_score'], reverse=True)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Statistics
        all_locations = []
        for article in protest_articles:
            all_locations.extend(article['location_analysis']['locations_found'])
        
        location_counts = {}
        for loc in all_locations:
            location_counts[loc] = location_counts.get(loc, 0) + 1
        
        protest_types = {}
        sources = {}
        for article in protest_articles:
            p_type = article['location_analysis']['protest_type']
            protest_types[p_type] = protest_types.get(p_type, 0) + 1
            
            source = article.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        logger.info(f"Found {len(protest_articles)} located protest articles")
        
        return {
            "success": True,
            "source": "Precision RSS Scraping",
            "working_feeds": len(working_feeds),
            "total_articles_collected": len(all_articles),
            "unique_articles": len(unique_articles),
            "articles_analyzed": len(articles_with_content),
            "located_protests_found": len(protest_articles),
            "filter_efficiency": round(len(protest_articles) / len(articles_with_content) * 100, 1) if articles_with_content else 0,
            "processing_time_seconds": round(processing_time, 2),
            "top_locations": dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "protest_types": protest_types,
            "sources": sources,
            "articles": protest_articles[:10]
        }


