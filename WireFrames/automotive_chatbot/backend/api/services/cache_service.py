import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from dataclasses import dataclass

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_keys: int = 0
    memory_usage: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

class CacheService:
    """Cache service with Redis backend and memory fallback"""
    
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self.use_redis = False
        self.stats = CacheStats()
        
        # Fallback in-memory cache
        self.fallback_cache: Dict[str, Any] = {}
        self.fallback_expiry: Dict[str, datetime] = {}
        
    async def initialize(self):
        """Initialize the cache service"""
        if REDIS_AVAILABLE and self.redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                # Test connection
                await self.redis_client.ping()
                self.use_redis = True
                logger.info("Cache service initialized with Redis backend")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using memory fallback.")
                self.use_redis = False
        else:
            logger.info("Cache service initialized with memory backend")
            self.use_redis = False
            
    async def close(self):
        """Close the cache service"""
        if self.redis_client:
            await self.redis_client.close()
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis and self.redis_client:
                value = await self.redis_client.get(key)
                if value is not None:
                    self.stats.hits += 1
                    return json.loads(value)
                else:
                    self.stats.misses += 1
                    return None
            else:
                # Use fallback cache
                await self._cleanup_expired_fallback()
                if key in self.fallback_cache:
                    self.stats.hits += 1
                    return self.fallback_cache[key]
                else:
                    self.stats.misses += 1
                    return None
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
            
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value)
            
            if self.use_redis and self.redis_client:
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                # Use fallback cache
                self.fallback_cache[key] = value
                self.fallback_expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
                
            self.stats.sets += 1
            return True
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.use_redis and self.redis_client:
                result = await self.redis_client.delete(key)
                deleted = result > 0
            else:
                # Use fallback cache
                deleted = key in self.fallback_cache
                if deleted:
                    del self.fallback_cache[key]
                    if key in self.fallback_expiry:
                        del self.fallback_expiry[key]
                        
            if deleted:
                self.stats.deletes += 1
            return deleted
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
            
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.use_redis and self.redis_client:
                return await self.redis_client.exists(key) > 0
            else:
                await self._cleanup_expired_fallback()
                return key in self.fallback_cache
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
            
    async def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.flushdb()
            else:
                self.fallback_cache.clear()
                self.fallback_expiry.clear()
            return True
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache clear error: {str(e)}")
            return False
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.use_redis and self.redis_client:
                info = await self.redis_client.info('memory')
                keyspace = await self.redis_client.info('keyspace')
                
                # Extract key count from keyspace info
                total_keys = 0
                for db_info in keyspace.values():
                    if isinstance(db_info, dict) and 'keys' in db_info:
                        total_keys += db_info['keys']
                        
                self.stats.total_keys = total_keys
                self.stats.memory_usage = info.get('used_memory', 0)
            else:
                await self._cleanup_expired_fallback()
                self.stats.total_keys = len(self.fallback_cache)
                # Estimate memory usage for fallback cache
                self.stats.memory_usage = sum(
                    len(str(k)) + len(str(v)) for k, v in self.fallback_cache.items()
                )
                
            return {
                'backend': 'redis' if self.use_redis else 'memory',
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'sets': self.stats.sets,
                'deletes': self.stats.deletes,
                'errors': self.stats.errors,
                'total_keys': self.stats.total_keys,
                'memory_usage_bytes': self.stats.memory_usage,
                'hit_rate_percent': self.stats.hit_rate
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                'backend': 'redis' if self.use_redis else 'memory',
                'error': str(e)
            }
            
    async def _cleanup_expired_fallback(self):
        """Clean up expired entries in fallback cache"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, expiry in self.fallback_expiry.items()
            if expiry <= now
        ]
        
        for key in expired_keys:
            if key in self.fallback_cache:
                del self.fallback_cache[key]
            if key in self.fallback_expiry:
                del self.fallback_expiry[key]
                
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the cache service"""
        try:
            test_key = 'health_check_test'
            test_value = {'timestamp': datetime.utcnow().isoformat()}
            
            # Test set and get
            await self.set(test_key, test_value, ttl=60)
            retrieved = await self.get(test_key)
            await self.delete(test_key)
            
            is_healthy = retrieved is not None
            
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'backend': 'redis' if self.use_redis else 'memory',
                'timestamp': datetime.utcnow().isoformat(),
                'stats': await self.get_stats()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'backend': 'redis' if self.use_redis else 'memory',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global cache service instance
_cache_service: Optional[CacheService] = None

async def initialize_cache_service(redis_url: str = None, default_ttl: int = 3600):
    """Initialize the global cache service"""
    global _cache_service
    _cache_service = CacheService(redis_url, default_ttl)
    await _cache_service.initialize()
    return _cache_service

def get_cache_service() -> CacheService:
    """Get the global cache service instance"""
    if _cache_service is None:
        raise RuntimeError("Cache service not initialized. Call initialize_cache_service() first.")
    return _cache_service

async def close_cache_service():
    """Close the global cache service"""
    global _cache_service
    if _cache_service:
        await _cache_service.close()
        _cache_service = None