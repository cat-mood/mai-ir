"""URL normalization utilities for consistent URL handling."""

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def normalize_url(url: str) -> str:
    """
    Normalize a URL for consistent storage and comparison.
    
    Steps:
    1. Parse the URL
    2. Convert scheme and domain to lowercase
    3. Remove fragment (#anchors)
    4. Sort query parameters alphabetically
    5. Remove trailing slash from path (except for root)
    
    Args:
        url: The URL to normalize
        
    Returns:
        The normalized URL string
    """
    if not url:
        return ""
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Convert scheme and netloc (domain) to lowercase
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Get path, remove trailing slash unless it's the root
    path = parsed.path
    if path and path != '/' and path.endswith('/'):
        path = path.rstrip('/')
    
    # Sort query parameters alphabetically
    query = parsed.query
    if query:
        # Parse query string into dict
        params = parse_qs(query, keep_blank_values=True)
        # Sort keys and rebuild query string
        sorted_params = sorted(params.items())
        query = urlencode(sorted_params, doseq=True)
    
    # Rebuild URL without fragment
    normalized = urlunparse((
        scheme,
        netloc,
        path,
        parsed.params,
        query,
        ''  # Remove fragment
    ))
    
    return normalized


def is_valid_url(url: str, domain_whitelist: list = None) -> bool:
    """
    Check if a URL is valid and optionally if it's in the domain whitelist.
    
    Args:
        url: The URL to validate
        domain_whitelist: Optional list of allowed domains
        
    Returns:
        True if the URL is valid (and in whitelist if provided), False otherwise
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Must be http or https
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Check domain whitelist if provided
        if domain_whitelist:
            domain = parsed.netloc.lower()
            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check if domain matches any in whitelist
            for allowed_domain in domain_whitelist:
                allowed = allowed_domain.lower()
                if allowed.startswith('www.'):
                    allowed = allowed[4:]
                
                if domain == allowed or domain.endswith('.' + allowed):
                    return True
            
            return False
        
        return True
        
    except Exception:
        return False


def get_domain(url: str) -> str:
    """
    Extract the domain from a URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        The domain string, or empty string if invalid
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""



