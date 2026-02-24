#!/usr/bin/env python3
"""
Bethesda.net Fallout Site Crawler
Recursively crawls the Fallout section of bethesda.net
"""

import time
import signal
import sys
from typing import Set, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from src.utils.url_normalizer import normalize_url, is_valid_url, get_domain
from src.db.db_manager import DatabaseManager
from src.fetchers.fetcher_factory import create_fetcher
from src.fetchers.base_fetcher import BaseFetcher


class BethesdaSiteCrawler:
    """Crawler for bethesda.net Fallout site with recursive link discovery."""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        """
        Initialize the crawler.
        
        Args:
            config: Configuration dict containing crawler settings
            db_manager: DatabaseManager instance
        """
        self.config = config
        self.db = db_manager
        self.fetcher: BaseFetcher = create_fetcher(config)
        
        # Crawler settings
        self.delay = config.get('logic', {}).get('delay_seconds', 2.0)
        self.recrawl_age_days = config.get('logic', {}).get('recrawl_age_days', 30)
        
        self.start_url = config.get('crawler', {}).get('start_url', '')
        self.domain_whitelist = config.get('crawler', {}).get('domain_whitelist', [])
        self.source_name = config.get('crawler', {}).get('source_name', 'Bethesda Fallout')
        self.source_domain = config.get('crawler', {}).get('source_domain', 'fallout.bethesda.net')
        self.max_depth = config.get('crawler', {}).get('max_depth', 5)
        
        # Get seed URLs (additional starting points)
        seed_urls = config.get('crawler', {}).get('seed_urls', [])
        initial_urls = set([self.start_url] + seed_urls)
        
        # State tracking
        self.should_stop = False
        self.visited_urls: Set[str] = set()
        self.urls_to_visit: Set[str] = initial_urls
        
        # Statistics
        self.pages_crawled = 0
        self.pages_updated = 0
        self.pages_skipped = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("\n⚠️  Received interrupt signal. Saving state and shutting down...")
        self.should_stop = True
    
    def extract_links(self, html: str, base_url: str) -> Set[str]:
        """
        Extract all internal links from HTML.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Set of normalized URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Resolve relative URLs
            if href.startswith('/'):
                full_url = f"https://{get_domain(base_url)}{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(base_url, href)
            
            # Normalize and validate
            normalized = normalize_url(full_url)
            if normalized and is_valid_url(normalized, self.domain_whitelist):
                # Skip common non-content URLs
                if self._is_content_url(normalized):
                    links.add(normalized)
        
        return links
    
    def _is_content_url(self, url: str) -> bool:
        """
        Check if URL is likely to contain content worth crawling.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL should be crawled
        """
        # Skip login, API, and other non-content URLs
        skip_patterns = [
            'login', 'logout', 'signin', 'signup', 'register',
            'api/', '.json', '.xml', '.pdf', '.zip',
            'mailto:', 'tel:', 'ftp:',
            '/search', '/redeem', '/account',
            'gear.bethesda.net', 'help.bethesda.net', 'status.bethesda.net',
            'accounts.bethesda.net', 'manuals.bethesda.net',
            'creations.bethesda.net', 'mods.bethesda.net',
            'slayersclub.bethesda.net', 'quakecon.bethesda.net',
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        return True
    
    def crawl_page(self, url: str, depth: int = 0):
        """
        Crawl a single page and discover new links.
        
        Args:
            url: URL of the page to crawl
            depth: Current recursion depth
        """
        if depth > self.max_depth:
            print(f"  ⏭️  Max depth reached for: {url}")
            return
        
        # Fetch page
        html = self.fetcher.fetch_page(url)
        if not html:
            return
        
        # Save to database if needed
        if self.db.document_needs_update(url, html, self.recrawl_age_days, self.source_domain):
            success = self.db.save_document(url, html, self.source_name, self.source_domain)
            if success:
                self.pages_updated += 1
                print(f"  ✅ [Depth {depth}] Saved: {url}")
            else:
                print(f"  ❌ [Depth {depth}] Failed to save: {url}")
        else:
            self.pages_skipped += 1
            print(f"  ⏭️  [Depth {depth}] Skipped (up-to-date): {url}")
        
        self.pages_crawled += 1
        
        # Extract new links
        new_links = self.extract_links(html, url)
        new_links_count = len(new_links - self.visited_urls - self.urls_to_visit)
        if new_links_count > 0:
            print(f"  🔗 Found {new_links_count} new links")
        
        # Add to queue
        self.urls_to_visit.update(new_links - self.visited_urls)
    
    def save_state(self):
        """Save current crawl state to database."""
        state = {
            'visited_count': len(self.visited_urls),
            'queue_count': len(self.urls_to_visit),
            'pages_crawled': self.pages_crawled,
            'pages_updated': self.pages_updated,
            'pages_skipped': self.pages_skipped,
        }
        self.db.save_crawl_state(state)
        print(f"💾 State saved (visited: {len(self.visited_urls)}, queue: {len(self.urls_to_visit)})")
    
    def run(self):
        """Main crawl loop."""
        print("=" * 60)
        print("🚀 Starting Bethesda Fallout Site Crawler")
        print("=" * 60)
        print(f"Starting URL: {self.start_url}")
        print(f"Max depth: {self.max_depth}")
        print(f"Domain whitelist: {self.domain_whitelist}")
        print()
        
        depth = 0
        
        while self.urls_to_visit and not self.should_stop:
            # Get next URL
            url = self.urls_to_visit.pop()
            
            if url in self.visited_urls:
                continue
            
            print(f"\n[{len(self.visited_urls) + 1}] Crawling: {url}")
            
            # Mark as visited
            self.visited_urls.add(url)
            
            # Crawl page
            self.crawl_page(url, depth)
            
            # Respect rate limit
            time.sleep(self.delay)
            
            # Save state periodically (every 10 pages)
            if len(self.visited_urls) % 10 == 0:
                self.save_state()
        
        # Final state save
        if not self.should_stop:
            print("\n" + "=" * 60)
            print("🎉 Crawl completed!")
        else:
            print("\n" + "=" * 60)
            print("⏸️  Crawl paused")
        
        print("=" * 60)
        print("📊 Final Statistics:")
        print(f"   - Total pages crawled: {self.pages_crawled}")
        print(f"   - Pages updated: {self.pages_updated}")
        print(f"   - Pages skipped: {self.pages_skipped}")
        print(f"   - URLs visited: {len(self.visited_urls)}")
        print(f"   - URLs in queue: {len(self.urls_to_visit)}")
        print(f"   - Total documents in DB: {self.db.get_document_count()}")
        print("=" * 60)
        
        self.save_state()
        self.fetcher.close()

