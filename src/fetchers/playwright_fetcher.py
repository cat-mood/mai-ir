"""Playwright-based page fetcher with anti-detection measures."""

import random
import time
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from src.fetchers.base_fetcher import BaseFetcher


# User-Agent rotation list
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]


class PlaywrightFetcher(BaseFetcher):
    """Fetcher using Playwright browser (slower, full browser simulation)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Playwright fetcher.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        
        # Browser configuration
        browser_config = config.get('browser', {})
        self.headless = browser_config.get('headless', True)
        self.browser_type = browser_config.get('browser_type', 'chromium')
        self.viewport_width = browser_config.get('viewport_width', 1920)
        self.viewport_height = browser_config.get('viewport_height', 1080)
        self.block_images = browser_config.get('block_images', True)
        self.block_ads = browser_config.get('block_ads', True)
        
        # Initialize Playwright
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        self._init_browser()
    
    def _init_browser(self):
        """Initialize Playwright browser with anti-detection measures."""
        print("🌐 Initializing Playwright browser...")
        
        self.playwright = sync_playwright().start()
        
        # Select browser type
        if self.browser_type == 'firefox':
            browser_type = self.playwright.firefox
        elif self.browser_type == 'webkit':
            browser_type = self.playwright.webkit
        else:
            browser_type = self.playwright.chromium
        
        # Launch browser with anti-detection and Docker-friendly args
        # Different browsers support different args
        if self.browser_type == 'firefox':
            # Firefox-specific args
            self.browser = browser_type.launch(
                headless=self.headless,
                firefox_user_prefs={
                    'dom.webdriver.enabled': False,
                    'useAutomationExtension': False,
                }
            )
        else:
            # Chromium/Chrome args
            self.browser = browser_type.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',  # Use /tmp instead of /dev/shm
                    '--no-sandbox',              # Required for Docker
                    '--disable-setuid-sandbox',  # Required for Docker
                    '--disable-gpu',             # Disable GPU in headless
                ]
            )
        
        # Create context with randomized settings
        viewport_width = self.viewport_width + random.randint(-50, 50)
        viewport_height = self.viewport_height + random.randint(-50, 50)
        
        self.context = self.browser.new_context(
            viewport={'width': viewport_width, 'height': viewport_height},
            user_agent=random.choice(USER_AGENTS),
            locale='en-US',
            timezone_id='America/New_York',
            permissions=[],
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        
        # Remove webdriver flag
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Block resources if configured
        if self.block_images or self.block_ads:
            def block_resources(route):
                resource_type = route.request.resource_type
                url = route.request.url
                
                # Block images
                if self.block_images and resource_type == 'image':
                    route.abort()
                    return
                
                # Block ads and analytics
                if self.block_ads:
                    ad_domains = [
                        'doubleclick.net',
                        'googlesyndication.com',
                        'googleadservices.com',
                        'google-analytics.com',
                        'googletagmanager.com',
                        'facebook.net',
                        'adservice.google.com',
                    ]
                    if any(domain in url for domain in ad_domains):
                        route.abort()
                        return
                
                route.continue_()
            
            self.context.route('**/*', block_resources)
        
        print("✅ Browser initialized successfully")

    @staticmethod
    def _is_challenge_page(html: str) -> bool:
        """Detect Cloudflare/interstitial challenge page markers."""
        html_lower = html.lower()
        markers = [
            'just a moment',
            'challenge-platform',
            'cf-chl',
            'attention required!',
            'checking if the site connection is secure',
            'please wait while we check your browser',
        ]
        return any(marker in html_lower for marker in markers)

    def _wait_for_challenge_resolution(self, page: Page) -> bool:
        """
        Wait until Cloudflare challenge disappears.

        Returns:
            True if challenge is resolved, False if still blocked.
        """
        max_wait_seconds = min(max(15, int(self.captcha_wait_minutes * 60)), 120)
        deadline = time.time() + max_wait_seconds

        while time.time() < deadline:
            html = page.content()
            if not self._is_challenge_page(html):
                return True
            page.wait_for_timeout(3000)

        return not self._is_challenge_page(page.content())
    
    def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fetch a page using Playwright browser.
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
            
        Returns:
            HTML content or None if failed
        """
        page: Optional[Page] = None
        
        try:
            # Create a new page
            page = self.context.new_page()
            
            # Fandom can keep background requests open, so waiting for full "load"
            # is often unstable. DOMContentLoaded is enough for parsing category links.
            response = None
            try:
                response = page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
            except PlaywrightTimeoutError:
                print(f"⚠️  DOMContentLoaded timeout at {url}. Proceeding with current page state...")
            
            if not response and page.url == 'about:blank':
                print(f"⚠️  No response from {url}")
                return None
            
            # Check for Cloudflare challenge and wait for real completion.
            if self._is_challenge_page(page.content()):
                print(f"🛡️  Cloudflare challenge detected, waiting for completion...")
                if self._wait_for_challenge_resolution(page):
                    print("✅ Cloudflare challenge completed")
                else:
                    raise RuntimeError("Cloudflare challenge did not complete in time")
            
            # Try to settle dynamic content, but do not fail hard if network stays busy.
            try:
                page.wait_for_load_state('networkidle', timeout=5000)
            except PlaywrightTimeoutError:
                pass
            page.wait_for_timeout(1000)
            
            # Get HTML content
            html = page.content()

            if self._is_challenge_page(html):
                raise RuntimeError("Received challenge page instead of content")
            
            return html
            
        except Exception as e:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                print(f"⚠️  Error fetching {url}: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self.fetch_page(url, retry_count + 1)
            else:
                print(f"❌ Failed to fetch {url} after {self.max_retries} retries: {e}")
                return None
        
        finally:
            # Always close the page to free resources
            if page:
                page.close()
    
    def close(self):
        """Clean up Playwright resources."""
        print("🔌 Closing Playwright browser...")
        
        if self.context:
            self.context.close()
        
        if self.browser:
            self.browser.close()
        
        if self.playwright:
            self.playwright.stop()
        
        print("✅ Browser closed")

