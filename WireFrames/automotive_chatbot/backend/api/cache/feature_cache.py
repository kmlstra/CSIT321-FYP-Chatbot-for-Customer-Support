import time
import threading
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from bson import ObjectId
from api.config.database import get_collection

logger = logging.getLogger(__name__)

class FeatureCache:
    """Thread-safe feature cache with TTL (Time To Live) functionality
    
    This cache stores client feature settings to reduce MongoDB queries.
    Features:
    - TTL expiration (default 10 minutes)
    - Thread-safe operations
    - Automatic cache refresh
    - Memory-efficient storage
    """
    
    def __init__(self, ttl_minutes: int = 10):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._ttl = timedelta(minutes=ttl_minutes)
        logger.info(f"FeatureCache initialized with TTL: {ttl_minutes} minutes")
    
    def _is_expired(self, client_id: str) -> bool:
        """Check if cache entry is expired"""
        if client_id not in self._timestamps:
            return True
        return datetime.now() - self._timestamps[client_id] > self._ttl
    
    def _fetch_features_from_db(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Fetch client feature settings from MongoDB Atlas"""
        try:
            clients_collection = get_collection('clients')
            if not clients_collection:
                logger.error("Failed to get clients collection")
                return None
            
            # Try to find client by ObjectId first, then by custom id, domain, or api_key
            client_doc = None
            try:
                # Try ObjectId first
                client_doc = clients_collection.find_one(
                    {"_id": ObjectId(client_id)},
                    {"settings.features": 1}  # Only fetch features to reduce data transfer
                )
            except:
                pass
            
            if not client_doc:
                # Try custom id, domain, or api_key
                client_doc = clients_collection.find_one(
                    {
                        "$or": [
                            {"id": client_id},
                            {"domain": client_id},
                            {"api_key": client_id}
                        ]
                    },
                    {"settings.features": 1}  # Only fetch features to reduce data transfer
                )
            
            if not client_doc:
                logger.warning(f"No client found for ID: {client_id}")
                return None
            
            # Extract feature settings with defaults
            features = client_doc.get('settings', {}).get('features', {})
            
            # Default feature settings
            default_features = {
                'live_support': True,
                'appointment_booking': False,  # Default to False, enable based on client configuration
                'coe_queries': True,
                'contact_support': True,
                'cached_at': datetime.now().isoformat()
            }
            
            # Merge with actual features
            feature_data = {**default_features, **features}
            
            logger.info(f"Successfully fetched feature data from MongoDB for client_id: {client_id}")
            return feature_data
            
        except Exception as e:
            logger.error(f"Error fetching feature data from MongoDB: {e}")
            return None
    
    def get_feature_setting(self, client_id: str, feature_name: str, default_value: bool = True) -> bool:
        """Get specific feature setting from cache or fetch from database if not cached/expired"""
        with self._lock:
            # Check if data exists and is not expired
            if client_id in self._cache and not self._is_expired(client_id):
                logger.debug(f"Feature cache hit for client_id: {client_id}")
                return self._cache[client_id].get(feature_name, default_value)
            
            # Cache miss or expired - fetch from database
            logger.debug(f"Feature cache miss for client_id: {client_id}, fetching from database")
            feature_data = self._fetch_features_from_db(client_id)
            
            if feature_data:
                # Store in cache
                self._cache[client_id] = feature_data
                self._timestamps[client_id] = datetime.now()
                logger.info(f"Cached feature data for client_id: {client_id}")
                return feature_data.get(feature_name, default_value)
            
            # Return default if fetch failed
            return default_value
    
    def get_all_features(self, client_id: str) -> Dict[str, Any]:
        """Get all feature settings for a client"""
        with self._lock:
            # Check if data exists and is not expired
            if client_id in self._cache and not self._is_expired(client_id):
                logger.debug(f"Feature cache hit for client_id: {client_id}")
                return self._cache[client_id].copy()
            
            # Cache miss or expired - fetch from database
            logger.debug(f"Feature cache miss for client_id: {client_id}, fetching from database")
            feature_data = self._fetch_features_from_db(client_id)
            
            if feature_data:
                # Store in cache
                self._cache[client_id] = feature_data
                self._timestamps[client_id] = datetime.now()
                logger.info(f"Cached feature data for client_id: {client_id}")
                return feature_data.copy()
            
            # Return defaults if fetch failed
            return {
                'live_support': True,
                'appointment_booking': False,  # Default to False, enable based on client configuration
                'coe_queries': True,
                'contact_support': True
            }
    
    def invalidate_client(self, client_id: str) -> None:
        """Invalidate cache entry for a specific client"""
        with self._lock:
            if client_id in self._cache:
                del self._cache[client_id]
                del self._timestamps[client_id]
                logger.info(f"Invalidated feature cache for client_id: {client_id}")
    
    def clear_cache(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            logger.info("Cleared all feature cache entries")
    
    def cleanup_expired(self) -> None:
        """Remove expired entries from cache"""
        with self._lock:
            expired_clients = []
            for client_id in list(self._cache.keys()):
                if self._is_expired(client_id):
                    expired_clients.append(client_id)
            
            for client_id in expired_clients:
                del self._cache[client_id]
                del self._timestamps[client_id]
            
            if expired_clients:
                logger.info(f"Cleaned up {len(expired_clients)} expired feature cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'total_entries': len(self._cache),
                'ttl_minutes': self._ttl.total_seconds() / 60,
                'cached_clients': list(self._cache.keys())
            }

# Global cache instance
_feature_cache = None
_cache_lock = threading.Lock()

def get_feature_cache() -> FeatureCache:
    """Get the global feature cache instance (singleton pattern)"""
    global _feature_cache
    if _feature_cache is None:
        with _cache_lock:
            if _feature_cache is None:
                _feature_cache = FeatureCache(ttl_minutes=10)
    return _feature_cache