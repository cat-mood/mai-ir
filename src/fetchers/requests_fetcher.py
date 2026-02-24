"""Requests-based page fetcher."""

import os
import sys
import time
import random
from typing import Optional, Dict, Any
import requests
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


class RequestsFetcher(BaseFetcher):
    """Fetcher using requests library (fast, no JavaScript support)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the requests fetcher.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        
        user_agent_config = config.get('logic', {}).get('user_agent', 'FalloutWikiCrawler/1.0')
        self.use_rotation = (user_agent_config == 'rotate')
        self.user_agent = user_agent_config if not self.use_rotation else None
        self.non_interactive = (
            os.getenv('NON_INTERACTIVE', '').strip().lower() in {'1', 'true', 'yes'}
            or not sys.stdin.isatty()
        )
    
    def get_user_agent(self) -> str:
        """Get User-Agent string (with rotation if enabled)."""
        if self.use_rotation:
            return random.choice(USER_AGENTS)
        return self.user_agent or 'FalloutWikiCrawler/1.0'
    
    def detect_captcha(self, html: str, status_code: int) -> bool:
        """
        Detect if the response contains a CAPTCHA.
        
        Args:
            html: HTML content
            status_code: HTTP status code
            
        Returns:
            True if CAPTCHA detected, False otherwise
        """
        if not html:
            return False

        html_lower = html.lower()

        # Require specific challenge markers to avoid false positives on normal pages.
        captcha_terms = [
            'captcha',
            'please verify you are a human',
            'verify you are human',
            'g-recaptcha',
            'hcaptcha',
        ]
        challenge_terms = [
            'cf-challenge',
            'challenge-platform',
            'challenges.cloudflare.com',
            'cf-ray',
            'ray id:',
            'attention required!',
        ]

        has_captcha_term = any(term in html_lower for term in captcha_terms)
        has_challenge_term = any(term in html_lower for term in challenge_terms)

        if status_code in (403, 429, 503):
            return has_captcha_term or has_challenge_term

        return has_captcha_term and has_challenge_term
    
    def handle_captcha(self, url: str):
        """
        Handle CAPTCHA detection - pause and notify user.
        
        Args:
            url: URL where CAPTCHA was encountered
        """
        print("\n" + "🚨" * 30)
        print("⚠️  CAPTCHA DETECTED!")
        print(f"URL: {url}")
        print("=" * 60)
        print("Действия:")
        print("1. Откройте URL в браузере и решите капчу")
        print("2. Подождите 5-10 минут")
        print("3. Нажмите Enter для продолжения или Ctrl+C для остановки")
        print("🚨" * 30 + "\n")
        
        if self.non_interactive:
            wait_seconds = max(1, int(self.captcha_wait_minutes * 60))
            print(
                f"⏳ Non-interactive mode detected. "
                f"Waiting {self.captcha_wait_minutes} minute(s) before retry..."
            )
            time.sleep(wait_seconds)
            print("✅ Retry after wait")
            return

        try:
            input("Нажмите Enter после решения капчи...")
            print("✅ Продолжаем работу...")
        except EOFError:
            wait_seconds = max(1, int(self.captcha_wait_minutes * 60))
            print(
                "\n⚠️  stdin недоступен. Переключаемся в non-interactive режим "
                f"и ждём {self.captcha_wait_minutes} minute(s)..."
            )
            time.sleep(wait_seconds)
            print("✅ Retry after wait")
        except KeyboardInterrupt:
            print("\n⏸️  Остановка по запросу пользователя")
            raise
    
    def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fetch a page with retries, error handling, and CAPTCHA detection.
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
            
        Returns:
            HTML content or None if failed
        """
        try:
            headers = {'User-Agent': self.get_user_agent()}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            # Check for CAPTCHA before raising for status
            if self.detect_captcha(response.text, response.status_code):
                if retry_count >= self.max_retries:
                    print(f"❌ CAPTCHA persists at {url}. Reached max retries: {self.max_retries}")
                    return None
                print(f"🚨 CAPTCHA detected at {url}")
                self.handle_captcha(url)
                # Try again after CAPTCHA resolution
                return self.fetch_page(url, retry_count + 1)
            
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
    
    def close(self):
        """Clean up resources (nothing to clean up for requests)."""
        pass

