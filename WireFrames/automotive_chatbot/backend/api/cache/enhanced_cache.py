"""Enhanced Cache Module
Provides advanced caching functionality with TTL support and async operations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Union
import threading
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    value: Any
    expires_at: datetime
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None

class EnhancedCache:
    """Enhanced cache with TTL, async support, and advanced features"""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Initialize enhanced cache
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of cache entries
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set cache value with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        created_at = datetime.now()
        
        with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size:
                self._evict_expired()
                if len(self._cache) >= self.max_size:
                    self._evict_lru()
            
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=expires_at,
                created_at=created_at
            )
            self._stats['sets'] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cache value
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            # Check if expired
            if datetime.now() > entry.expires_at:
                del self._cache[key]
                self._stats['misses'] += 1
                return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            self._stats['hits'] += 1
            
            return entry.value
    
    def delete(self, key: str) -> bool:
        """
        Delete cache entry
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0,
                'evictions': 0
            }
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired
        
        Args:
            key: Cache key
            
        Returns:
            True if exists and not expired
        """
        return self.get(key) is not None
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds or None if not found
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            remaining = (entry.expires_at - datetime.now()).total_seconds()
            return max(0, int(remaining))
    
    def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """
        Extend TTL for a key
        
        Args:
            key: Cache key
            additional_seconds: Additional seconds to add
            
        Returns:
            True if extended, False if not found
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            entry.expires_at += timedelta(seconds=additional_seconds)
            return True
    
    async def get_or_set(self, key: str, fetch_func, ttl: Optional[int] = None) -> Any:
        """
        Get from cache or fetch and cache
        
        Args:
            key: Cache key
            fetch_func: Function to fetch value if not in cache
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or fetched value
        """
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Fetch new value
        if asyncio.iscoroutinefunction(fetch_func):
            new_value = await fetch_func()
        else:
            new_value = fetch_func()
        
        self.set(key, new_value, ttl)
        return new_value
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self._stats,
                'total_requests': total_requests,
                'hit_rate_percent': round(hit_rate, 2),
                'cache_size': len(self._cache),
                'max_size': self.max_size
            }
    
    def _evict_expired(self) -> None:
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry.expires_at
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['evictions'] += 1
    
    def _evict_lru(self) -> None:
        """Remove least recently used entries"""
        if not self._cache:
            return
        
        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed or x[1].created_at
        )
        
        # Remove oldest 10% of entries
        num_to_remove = max(1, len(self._cache) // 10)
        for i in range(num_to_remove):
            if i < len(sorted_entries):
                key = sorted_entries[i][0]
                del self._cache[key]
                self._stats['evictions'] += 1
    
    def cleanup(self) -> int:
        """
        Manual cleanup of expired entries
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            initial_size = len(self._cache)
            self._evict_expired()
            return initial_size - len(self._cache)

# Global enhanced cache instance
enhanced_cache = EnhancedCache(default_ttl=300, max_size=1000)

# Cleanup task for periodic maintenance
async def periodic_cleanup():
    """Periodic cleanup task"""
    while True:
        try:
            removed = enhanced_cache.cleanup()
            if removed > 0:
                logger.debug(f"Enhanced cache cleanup: removed {removed} expired entries")
            await asyncio.sleep(60)  # Run every minute
        except Exception as e:
            logger.error(f"Error in enhanced cache cleanup: {e}")
            await asyncio.sleep(60)

# Start cleanup task
def start_cleanup_task():
    """Start the cleanup task"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(periodic_cleanup())
    except RuntimeError:
        # No event loop running, will start when one is available
        pass

# Auto-start cleanup when module is imported
start_cleanup_task()