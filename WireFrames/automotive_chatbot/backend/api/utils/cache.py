"""Simple in-memory cache for performance optimization"""

import time
from typing import Any, Dict, Optional
from threading import Lock

class SimpleCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if time.time() > entry['expires_at']:
                del self._cache[key]
                return None
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> None:
        """Remove expired entries"""
        current_time = time.time()
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry['expires_at']
            ]
            for key in expired_keys:
                del self._cache[key]

# Global cache instances with optimized TTL for performance
coe_cache = SimpleCache(default_ttl=300)  # 5 minutes for COE data (less frequent updates)
appointment_cache = SimpleCache(default_ttl=30)  # 30 seconds for appointment types
client_cache = SimpleCache(default_ttl=1800)  # 30 minutes for client data
response_cache = SimpleCache(default_ttl=120)  # 2 minutes for common responses
contact_cache = SimpleCache(default_ttl=3600)  # 1 hour for contact info (rarely changes)