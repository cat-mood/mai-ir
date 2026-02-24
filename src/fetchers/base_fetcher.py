"""Base class for page fetchers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseFetcher(ABC):
    """Abstract base class for page fetchers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the fetcher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.timeout = config.get('logic', {}).get('timeout_seconds', 30)
        self.max_retries = config.get('logic', {}).get('max_retries', 3)
        self.captcha_wait_minutes = config.get('logic', {}).get('captcha_wait_minutes', 10)
    
    @abstractmethod
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page and return its HTML content.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string, or None if fetch failed
        """
        pass
    
    @abstractmethod
    def close(self):
        """Clean up resources (e.g., close browser)."""
        pass

