"""Enhanced Cache System with TTL and Auto-cleanup
Provides high-performance caching for RASA Actions
"""

import asyncio
import time
import logging
from typing import Any, Optional, Dict, Callable, Union
from functools import wraps
import json
import hashlib
from threading import Lock
from dataclasses import dataclass
from collections import defaultdict

# Configure logging
logger = logging.getLogger('api.utils.enhanced_cache')
logger.setLevel(logging.DEBUG)

@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    value: Any
    created_at: float
    ttl: float
    access_count: int = 0
    last_accessed: float = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl <= 0:  # No expiration
            return False
        return time.time() > (self.created_at + self.ttl)
    
    def access(self) -> Any:
        """Access the cached value and update stats"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value

class EnhancedCache:
    """High-performance cache with TTL, auto-cleanup, and statistics
    
    Features:
    - TTL (Time To Live) support
    - Automatic cleanup of expired entries
    - LRU-style eviction when cache is full
    - Access statistics and monitoring
    - Thread-safe operations
    - Async support
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600, cleanup_interval: float = 300):
        """Initialize the enhanced cache
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds (0 = no expiration)
            cleanup_interval: Cleanup interval in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'cleanups': 0,
            'evictions': 0
        }
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
        
        logger.info(f"EnhancedCache initialized: max_size={max_size}, default_ttl={default_ttl}s")
    
    def _start_cleanup_task(self):
        """Start the automatic cleanup task"""
        if self.cleanup_interval > 0:
            try:
                loop = asyncio.get_event_loop()
                self._cleanup_task = loop.create_task(self._periodic_cleanup())
            except RuntimeError:
                # No event loop running, cleanup will be manual
                logger.warning("No event loop found, automatic cleanup disabled")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired entries"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def _generate_key(self, key: Union[str, tuple, dict]) -> str:
        """Generate a consistent cache key from various input types"""
        if isinstance(key, str):
            return key
        elif isinstance(key, (tuple, list)):
            return hashlib.md5(str(sorted(key)).encode()).hexdigest()
        elif isinstance(key, dict):
            return hashlib.md5(json.dumps(key, sort_keys=True).encode()).hexdigest()
        else:
            return hashlib.md5(str(key).encode()).hexdigest()
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].last_accessed or self._cache[k].created_at)
        
        del self._cache[lru_key]
        self._stats['evictions'] += 1
        logger.debug(f"Evicted LRU entry: {lru_key}")
    
    async def set(self, key: Union[str, tuple, dict], value: Any, ttl: Optional[float] = None) -> None:
        """Set a cache entry with optional TTL
        
        Args:
            key: Cache key (string, tuple, or dict)
            value: Value to cache
            ttl: Time to live in seconds (None = use default)
        """
        cache_key = self._generate_key(key)
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_lru()
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=effective_ttl,
                last_accessed=time.time()
            )
            
            self._cache[cache_key] = entry
            self._stats['sets'] += 1
            
        logger.debug(f"Cached entry: {cache_key} (TTL: {effective_ttl}s)")
    
    async def get(self, key: Union[str, tuple, dict], default: Any = None) -> Any:
        """Get a cache entry
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        cache_key = self._generate_key(key)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._stats['misses'] += 1
                logger.debug(f"Cache miss: {cache_key}")
                return default
            
            if entry.is_expired():
                del self._cache[cache_key]
                self._stats['misses'] += 1
                logger.debug(f"Cache expired: {cache_key}")
                return default
            
            self._stats['hits'] += 1
            logger.debug(f"Cache hit: {cache_key}")
            return entry.access()
    
    async def get_or_set(self, key: Union[str, tuple, dict], factory: Callable, ttl: Optional[float] = None) -> Any:
        """Get cached value or set it using factory function
        
        Args:
            key: Cache key
            factory: Function to generate value if not cached
            ttl: Time to live in seconds
            
        Returns:
            Cached or newly generated value
        """
        # Try to get existing value
        value = await self.get(key)
        if value is not None:
            return value
        
        # Generate new value
        try:
            if asyncio.iscoroutinefunction(factory):
                new_value = await factory()
            else:
                new_value = factory()
            
            # Cache the new value
            await self.set(key, new_value, ttl)
            return new_value
            
        except Exception as e:
            logger.error(f"Error in cache factory function: {e}")
            raise
    
    async def delete(self, key: Union[str, tuple, dict]) -> bool:
        """Delete a cache entry
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        cache_key = self._generate_key(key)
        
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                self._stats['deletes'] += 1
                logger.debug(f"Deleted cache entry: {cache_key}")
                return True
            return False
    
    async def cleanup_expired(self) -> int:
        """Remove all expired entries
        
        Returns:
            Number of entries removed
        """
        removed_count = 0
        current_time = time.time()
        
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1
            
            if removed_count > 0:
                self._stats['cleanups'] += 1
                logger.debug(f"Cleaned up {removed_count} expired entries")
        
        return removed_count
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests,
                **self._stats
            }
    
    def __del__(self):
        """Cleanup when cache is destroyed"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

# Global cache instance
_global_cache = None

def get_cache() -> EnhancedCache:
    """Get the global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = EnhancedCache()
    return _global_cache

# Decorator for caching function results
def cache_result(ttl: Optional[float] = None, key_prefix: str = ""):
    """Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.append(json.dumps(kwargs, sort_keys=True))
            
            cache_key = ":".join(filter(None, key_parts))
            
            # Try to get cached result
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, avoid event loop conflicts
            try:
                # Check if we're in an async context
                asyncio.get_running_loop()
                # We're in an async context, execute function directly without caching
                return func(*args, **kwargs)
            except RuntimeError:
                # No running loop, safe to use asyncio.run for caching
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(async_wrapper(*args, **kwargs))
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)
                except Exception:
                    # Fallback: execute function directly
                    return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# Convenience functions
async def cache_set(key: Union[str, tuple, dict], value: Any, ttl: Optional[float] = None):
    """Set cache entry using global cache"""
    cache = get_cache()
    await cache.set(key, value, ttl)

async def cache_get(key: Union[str, tuple, dict], default: Any = None) -> Any:
    """Get cache entry using global cache"""
    cache = get_cache()
    return await cache.get(key, default)

async def cache_delete(key: Union[str, tuple, dict]) -> bool:
    """Delete cache entry using global cache"""
    cache = get_cache()
    return await cache.delete(key)