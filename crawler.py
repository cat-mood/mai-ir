"""Web crawler for Fallout Wiki."""

import time
import signal
import sys
from typing import List, Set, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from url_normalizer import normalize_url, is_valid_url, get_domain
from db_manager import DatabaseManager


class FalloutWikiCrawler:
    """Crawler for Fallout Wiki with resumability and change detection."""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        """
        Initialize the crawler.
        
        Args:
            config: Configuration dict containing crawler settings
            db_manager: DatabaseManager instance
        """
        self.config = config
        self.db = db_manager
        
        # Crawler settings
        self.delay = config.get('logic', {}).get('delay_seconds', 1.0)
        self.recrawl_age_days = config.get('logic', {}).get('recrawl_age_days', 30)
        self.user_agent = config.get('logic', {}).get('user_agent', 'FalloutWikiCrawler/1.0')
        self.max_retries = config.get('logic', {}).get('max_retries', 3)
        self.timeout = config.get('logic', {}).get('timeout_seconds', 30)
        
        self.start_url = config.get('crawler', {}).get('start_url', '')
        self.domain_whitelist = config.get('crawler', {}).get('domain_whitelist', [])
        
        # State tracking
        self.should_stop = False
        self.categories: List[str] = []
        self.current_category_index = 0
        self.current_article_index = 0
        self.visited_urls: Set[str] = set()
        
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
        
    def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fetch a page with retries and error handling.
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
            
        Returns:
            HTML content or None if failed
        """
        try:
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.RequestException as e:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                print(f"⚠️  Error fetching {url}: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self.fetch_page(url, retry_count + 1)
            else:
                print(f"❌ Failed to fetch {url} after {self.max_retries} retries: {e}")
                return None
                
    def extract_category_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract category links from the Special:Categories page.
        
        Args:
            html: HTML content of the categories page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of category page URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        category_links = []
        
        # Find all links on the page
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Check if it's a category link (both relative and absolute formats)
            is_category = False
            if href.startswith('/wiki/Category:'):
                is_category = True
                full_url = f"https://{get_domain(base_url)}{href}"
            elif 'wiki/Category:' in href and href.startswith('http'):
                is_category = True
                full_url = href
            
            if is_category:
                normalized = normalize_url(full_url)
                if normalized and is_valid_url(normalized, self.domain_whitelist):
                    if normalized not in category_links:  # Avoid duplicates
                        category_links.append(normalized)
        
        return category_links
    
    def extract_pagination_next(self, html: str, base_url: str) -> Optional[str]:
        """
        Extract the "next" pagination link from a page.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Next page URL or None if no next page
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for MediaWiki pagination link with class 'mw-nextlink'
        next_link = soup.find('a', class_='mw-nextlink')
        if next_link:
            href = next_link.get('href', '')
            if href:
                # Handle relative URLs
                if href.startswith('/'):
                    full_url = f"https://{get_domain(base_url)}{href}"
                elif href.startswith('http'):
                    full_url = href
                else:
                    return None
                
                normalized = normalize_url(full_url)
                if normalized and is_valid_url(normalized, self.domain_whitelist):
                    return normalized
        
        # Fallback: look for links with "next" text
        links = soup.find_all('a')
        for link in links:
            text = link.get_text(strip=True).lower()
            if 'next' in text and any(char.isdigit() for char in text):
                href = link.get('href', '')
                if href:
                    # Handle relative URLs
                    if href.startswith('/'):
                        full_url = f"https://{get_domain(base_url)}{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    normalized = normalize_url(full_url)
                    if normalized and is_valid_url(normalized, self.domain_whitelist):
                        return normalized
        
        return None
    
    def extract_article_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract article links from a category page.
        
        Args:
            html: HTML content of category page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of article URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        article_links = []
        seen_urls = set()  # To avoid duplicates
        
        # Fandom uses 'category-page__members' class
        category_content = soup.find('div', class_='category-page__members')
        
        # Fallback to MediaWiki standard classes
        if not category_content:
            category_content_list = soup.find_all(['div', 'ul'], class_=['mw-category', 'mw-category-group'])
            if category_content_list:
                # Create a wrapper to iterate uniformly
                for content in category_content_list:
                    links = content.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if href and href.startswith('/wiki/') and ':' not in href.split('/wiki/')[1]:
                            full_url = f"https://{get_domain(base_url)}{href}"
                            normalized = normalize_url(full_url)
                            if normalized and is_valid_url(normalized, self.domain_whitelist):
                                if normalized not in seen_urls:
                                    article_links.append(normalized)
                                    seen_urls.add(normalized)
        else:
            # Extract links from Fandom category page
            links = category_content.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                
                # Handle both relative and absolute URLs
                if href.startswith('/wiki/'):
                    # Relative URL
                    path = href[6:]  # Remove '/wiki/'
                    # Skip special pages (they contain ':')
                    if ':' not in path:
                        full_url = f"https://{get_domain(base_url)}{href}"
                        normalized = normalize_url(full_url)
                        if normalized and is_valid_url(normalized, self.domain_whitelist):
                            if normalized not in seen_urls:
                                article_links.append(normalized)
                                seen_urls.add(normalized)
                elif 'wiki/' in href and href.startswith('http'):
                    # Absolute URL
                    parts = href.split('/wiki/')
                    if len(parts) > 1:
                        path = parts[1]
                        if ':' not in path:
                            normalized = normalize_url(href)
                            if normalized and is_valid_url(normalized, self.domain_whitelist):
                                if normalized not in seen_urls:
                                    article_links.append(normalized)
                                    seen_urls.add(normalized)
        
        return article_links
    
    def crawl_all_categories_from_start_url(self):
        """Crawl all category pages with pagination from the start URL."""
        print(f"🔍 Fetching categories from {self.start_url}")
        
        current_page_url = self.start_url
        page_num = 1
        
        while current_page_url and not self.should_stop:
            print(f"📄 Fetching categories page {page_num}...")
            
            html = self.fetch_page(current_page_url)
            if not html:
                break
            
            # Extract category links from this page
            category_links = self.extract_category_links(html, current_page_url)
            self.categories.extend(category_links)
            print(f"✅ Found {len(category_links)} categories on page {page_num}")
            
            # Check for next page
            next_page = self.extract_pagination_next(html, current_page_url)
            if next_page and next_page not in self.visited_urls:
                current_page_url = next_page
                self.visited_urls.add(current_page_url)
                page_num += 1
                time.sleep(self.delay)
            else:
                break
        
        print(f"📊 Total categories found: {len(self.categories)}")
    
    def crawl_category(self, category_url: str) -> List[str]:
        """
        Crawl all articles from a category page (with pagination).
        
        Args:
            category_url: URL of the category page
            
        Returns:
            List of article URLs found in the category
        """
        articles = []
        current_page = category_url
        page_num = 1
        
        while current_page and not self.should_stop:
            if page_num > 1:
                print(f"  📄 Fetching category page {page_num}...")
            
            html = self.fetch_page(current_page)
            if not html:
                break
            
            # Extract article links
            article_links = self.extract_article_links(html, current_page)
            articles.extend(article_links)
            
            # Check for next page in category
            next_page = self.extract_pagination_next(html, current_page)
            if next_page and next_page not in self.visited_urls:
                current_page = next_page
                self.visited_urls.add(current_page)
                page_num += 1
                time.sleep(self.delay)
            else:
                break
        
        return articles
    
    def crawl_article(self, article_url: str):
        """
        Crawl a single article and save to database if needed.
        
        Args:
            article_url: URL of the article to crawl
        """
        # Check if we need to crawl this article
        html = self.fetch_page(article_url)
        if not html:
            return
        
        # Check if document needs update
        if self.db.document_needs_update(article_url, html, self.recrawl_age_days):
            success = self.db.save_document(article_url, html)
            if success:
                self.pages_updated += 1
                print(f"  ✅ Saved: {article_url}")
            else:
                print(f"  ❌ Failed to save: {article_url}")
        else:
            self.pages_skipped += 1
            print(f"  ⏭️  Skipped (up-to-date): {article_url}")
        
        self.pages_crawled += 1
    
    def save_state(self):
        """Save current crawl state to database."""
        state = {
            'current_category_index': self.current_category_index,
            'current_category_url': self.categories[self.current_category_index] if self.current_category_index < len(self.categories) else None,
            'current_article_index': self.current_article_index,
            'total_categories': len(self.categories),
            'pages_crawled': self.pages_crawled,
            'pages_updated': self.pages_updated,
            'pages_skipped': self.pages_skipped,
        }
        self.db.save_crawl_state(state)
        print(f"💾 State saved (category {self.current_category_index + 1}/{len(self.categories)})")
    
    def load_state(self) -> bool:
        """
        Load previous crawl state from database.
        
        Returns:
            True if state was loaded, False if starting fresh
        """
        state = self.db.get_crawl_state()
        if state:
            self.current_category_index = state.get('current_category_index', 0)
            self.current_article_index = state.get('current_article_index', 0)
            self.pages_crawled = state.get('pages_crawled', 0)
            self.pages_updated = state.get('pages_updated', 0)
            self.pages_skipped = state.get('pages_skipped', 0)
            
            print(f"📂 Loaded previous state:")
            print(f"   - Category: {self.current_category_index + 1}/{state.get('total_categories', '?')}")
            print(f"   - Pages crawled: {self.pages_crawled}")
            print(f"   - Pages updated: {self.pages_updated}")
            print(f"   - Pages skipped: {self.pages_skipped}")
            return True
        
        return False
    
    def run(self):
        """Main crawl loop."""
        print("=" * 60)
        print("🚀 Starting Fallout Wiki Crawler")
        print("=" * 60)
        
        # Try to load previous state
        has_state = self.load_state()
        
        # If no state or starting fresh, get all categories
        if not has_state or not self.categories:
            self.crawl_all_categories_from_start_url()
            if not self.categories:
                print("❌ No categories found. Exiting.")
                return
        
        # Crawl each category
        total_categories = len(self.categories)
        
        for cat_idx in range(self.current_category_index, total_categories):
            if self.should_stop:
                break
            
            self.current_category_index = cat_idx
            category_url = self.categories[cat_idx]
            
            print(f"\n{'=' * 60}")
            print(f"📂 Category {cat_idx + 1}/{total_categories}: {category_url}")
            print(f"{'=' * 60}")
            
            # Get all articles in this category
            articles = self.crawl_category(category_url)
            print(f"📊 Found {len(articles)} articles in category")
            
            # Crawl each article
            start_article_idx = self.current_article_index if cat_idx == self.current_category_index else 0
            
            for art_idx in range(start_article_idx, len(articles)):
                if self.should_stop:
                    break
                
                self.current_article_index = art_idx
                article_url = articles[art_idx]
                
                print(f"  [{art_idx + 1}/{len(articles)}] Crawling: {article_url}")
                self.crawl_article(article_url)
                
                # Respect rate limit
                time.sleep(self.delay)
                
                # Save state periodically (every 10 articles)
                if (art_idx + 1) % 10 == 0:
                    self.save_state()
            
            # Reset article index for next category
            self.current_article_index = 0
            
            # Save state after completing a category
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
        print(f"   - Total documents in DB: {self.db.get_document_count()}")
        print("=" * 60)
        
        self.save_state()

