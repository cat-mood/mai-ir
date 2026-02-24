"""MongoDB database manager for the crawler."""

import hashlib
import time
from typing import Optional, Dict, Any
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database


class DatabaseManager:
    """Manages MongoDB operations for the web crawler."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the database connection.
        
        Args:
            config: Complete configuration dict including:
                   - db: Database configuration
                   - crawler: Crawler configuration (for crawler_id)
        """
        self.config = config
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.documents: Optional[Collection] = None
        self.crawl_state: Optional[Collection] = None
        self.crawler_id = config.get('crawler', {}).get('crawler_id', 'main_crawler')
        
    def connect(self):
        """Establish connection to MongoDB."""
        db_config = self.config.get('db', {})
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', 27017)
        username = db_config.get('username')
        password = db_config.get('password')
        database = db_config.get('database', 'fallout_wiki')
        
        # Build connection string
        if username and password:
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/"
        else:
            connection_string = f"mongodb://{host}:{port}/"
        
        self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test connection
        self.client.server_info()
        
        self.db = self.client[database]
        self.documents = self.db['documents']
        self.crawl_state = self.db['crawl_state']
        
        # Create indexes for better performance
        self._create_indexes()
        
    def _create_indexes(self):
        """Create necessary indexes on collections."""
        # Composite unique index on (url, source_domain) - allows same URL from different sources
        try:
            self.documents.create_index(
                [('url', ASCENDING), ('source_domain', ASCENDING)],
                unique=True,
                name='url_1_source_domain_1'
            )
        except Exception:
            # Index may already exist
            pass
        
        # Index on timestamp for age-based queries
        self.documents.create_index([('timestamp', ASCENDING)])
        
        # Index on source_domain for filtering by source
        self.documents.create_index([('source_domain', ASCENDING)])
        
    def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            
    def save_document(self, url: str, html: str, source: str, source_domain: str) -> bool:
        """
        Save or update a document in the database.
        
        Args:
            url: Normalized URL of the document
            html: Raw HTML content
            source: Source name (e.g., "Fallout Fandom")
            source_domain: Source domain (e.g., "fallout.fandom.com")
            
        Returns:
            True if document was saved/updated, False otherwise
        """
        try:
            content_hash = self._compute_hash(html)
            timestamp = int(time.time())
            
            # Use composite key (url, source_domain) for upsert
            self.documents.update_one(
                {'url': url, 'source_domain': source_domain},
                {
                    '$set': {
                        'html': html,
                        'source': source,
                        'source_domain': source_domain,
                        'timestamp': timestamp,
                        'content_hash': content_hash
                    }
                },
                upsert=True
            )
            return True
            
        except Exception as e:
            print(f"Error saving document {url}: {e}")
            return False
    
    def get_document(self, url: str, source_domain: str = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from the database by URL and optionally source_domain.
        
        Args:
            url: Normalized URL of the document
            source_domain: Optional source domain filter
            
        Returns:
            Document dict or None if not found
        """
        try:
            query = {'url': url}
            if source_domain:
                query['source_domain'] = source_domain
            return self.documents.find_one(query)
        except Exception as e:
            print(f"Error getting document {url}: {e}")
            return None
    
    def document_needs_update(self, url: str, new_html: str, max_age_days: int = 30, 
                             source_domain: str = None) -> bool:
        """
        Check if a document needs to be updated.
        
        A document needs update if:
        1. It doesn't exist in the database
        2. The content has changed (different hash)
        3. It's older than max_age_days
        
        Args:
            url: Normalized URL of the document
            new_html: New HTML content to compare
            max_age_days: Maximum age in days before re-crawling
            source_domain: Source domain to check
            
        Returns:
            True if document should be updated, False otherwise
        """
        doc = self.get_document(url, source_domain)
        
        # Document doesn't exist, needs to be saved
        if not doc:
            return True
        
        # Check if content changed
        new_hash = self._compute_hash(new_html)
        if doc.get('content_hash') != new_hash:
            return True
        
        # Check age
        current_time = int(time.time())
        doc_age_seconds = current_time - doc.get('timestamp', 0)
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        if doc_age_seconds > max_age_seconds:
            return True
        
        return False
    
    def save_crawl_state(self, state: Dict[str, Any]):
        """
        Save the current crawl state using crawler-specific ID.
        
        Args:
            state: State dict containing crawler position info
        """
        try:
            state['last_updated'] = int(time.time())
            
            self.crawl_state.update_one(
                {'_id': self.crawler_id},
                {'$set': state},
                upsert=True
            )
        except Exception as e:
            print(f"Error saving crawl state: {e}")
    
    def get_crawl_state(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the saved crawl state for this crawler.
        
        Returns:
            State dict or None if no state exists
        """
        try:
            return self.crawl_state.find_one({'_id': self.crawler_id})
        except Exception as e:
            print(f"Error getting crawl state: {e}")
            return None
    
    def clear_crawl_state(self):
        """Clear the crawl state for this crawler (start fresh)."""
        try:
            self.crawl_state.delete_one({'_id': self.crawler_id})
        except Exception as e:
            print(f"Error clearing crawl state: {e}")
    
    def get_document_count(self) -> int:
        """
        Get the total number of documents in the database.
        
        Returns:
            Count of documents
        """
        try:
            return self.documents.count_documents({})
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0
    
    @staticmethod
    def _compute_hash(content: str) -> str:
        """
        Compute MD5 hash of content.
        
        Args:
            content: String content to hash
            
        Returns:
            MD5 hash as hex string
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()



