"""Factory for creating page fetchers."""

from typing import Dict, Any
from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.requests_fetcher import RequestsFetcher
from src.fetchers.playwright_fetcher import PlaywrightFetcher


def create_fetcher(config: Dict[str, Any]) -> BaseFetcher:
    """
    Create a fetcher based on configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        An instance of BaseFetcher (either RequestsFetcher or PlaywrightFetcher)
    """
    fetch_method = config.get('crawler', {}).get('fetch_method', 'requests')
    
    if fetch_method == 'playwright':
        print("🌐 Using Playwright fetcher (browser-based)")
        return PlaywrightFetcher(config)
    else:
        print("⚡ Using Requests fetcher (fast, lightweight)")
        return RequestsFetcher(config)

