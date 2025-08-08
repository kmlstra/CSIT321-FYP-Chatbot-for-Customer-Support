"""
LTA API Rate Limiter and Caching Utility
Prevents API abuse and potential banning from LTA DataMall
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class LTAAPIRateLimiter:
    """
    Rate limiter for LTA API calls to prevent abuse and banning
    """
    
    def __init__(self, max_requests_per_hour: int = 100, min_interval_seconds: int = 10):
        self.max_requests_per_hour = max_requests_per_hour
        self.min_interval_seconds = min_interval_seconds
        self.request_history = []
        self.last_request_time = 0
        self.cache = {}
        self.cache_expiry = {}
        
    def _clean_old_requests(self):
        """Remove requests older than 1 hour"""
        current_time = time.time()
        one_hour_ago = current_time - 3600
        self.request_history = [req_time for req_time in self.request_history if req_time > one_hour_ago]
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without violating rate limits"""
        current_time = time.time()
        
        # Check minimum interval between requests
        if current_time - self.last_request_time < self.min_interval_seconds:
            logger.warning(f"Rate limit: Must wait {self.min_interval_seconds} seconds between requests")
            return False
        
        # Clean old requests and check hourly limit
        self._clean_old_requests()
        if len(self.request_history) >= self.max_requests_per_hour:
            logger.warning(f"Rate limit: Exceeded {self.max_requests_per_hour} requests per hour")
            return False
        
        return True
    
    def record_request(self):
        """Record that a request was made"""
        current_time = time.time()
        self.request_history.append(current_time)
        self.last_request_time = current_time
        logger.info(f"LTA API request recorded. Total requests in last hour: {len(self.request_history)}")
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict[Any, Any]]:
        """Get cached data if still valid"""
        if cache_key in self.cache:
            expiry_time = self.cache_expiry.get(cache_key, 0)
            if time.time() < expiry_time:
                logger.info(f"Returning cached data for {cache_key}")
                return self.cache[cache_key]
            else:
                # Remove expired cache
                del self.cache[cache_key]
                del self.cache_expiry[cache_key]
                logger.info(f"Cache expired for {cache_key}")
        return None
    
    def set_cache_data(self, cache_key: str, data: Dict[Any, Any], cache_minutes: int = 30):
        """Cache data for specified minutes"""
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = time.time() + (cache_minutes * 60)
        logger.info(f"Data cached for {cache_key} for {cache_minutes} minutes")
    
    def get_wait_time(self) -> int:
        """Get how long to wait before next request"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval_seconds:
            return int(self.min_interval_seconds - time_since_last)
        
        return 0

# Global rate limiter instance
lta_rate_limiter = LTAAPIRateLimiter()

def rate_limited_lta_request(cache_key: Optional[str] = None, cache_minutes: int = 30):
    """
    Decorator for LTA API requests with rate limiting and caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check cache first
            if cache_key:
                cached_data = lta_rate_limiter.get_cached_data(cache_key)
                if cached_data:
                    return cached_data
            
            # Check rate limit
            if not lta_rate_limiter.can_make_request():
                wait_time = lta_rate_limiter.get_wait_time()
                logger.warning(f"Rate limit exceeded. Wait {wait_time} seconds before next request")
                # Return cached data if available, even if expired
                if cache_key and cache_key in lta_rate_limiter.cache:
                    logger.info("Returning expired cache due to rate limit")
                    return lta_rate_limiter.cache[cache_key]
                raise Exception(f"Rate limit exceeded. Please wait {wait_time} seconds")
            
            # Make the request
            try:
                lta_rate_limiter.record_request()
                result = func(*args, **kwargs)
                
                # Cache the result
                if cache_key and result:
                    lta_rate_limiter.set_cache_data(cache_key, result, cache_minutes)
                
                return result
            except Exception as e:
                logger.error(f"LTA API request failed: {e}")
                # Return cached data if available
                if cache_key and cache_key in lta_rate_limiter.cache:
                    logger.info("Returning cached data due to API error")
                    return lta_rate_limiter.cache[cache_key]
                raise
        
        return wrapper
    return decorator