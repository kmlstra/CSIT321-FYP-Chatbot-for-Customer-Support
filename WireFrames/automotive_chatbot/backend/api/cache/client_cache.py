import time
import threading
import asyncio
from typing import Dict, Optional, Any, Set
from datetime import datetime, timedelta
import logging
from bson import ObjectId
from concurrent.futures import ThreadPoolExecutor
from api.config.database import get_collection

logger = logging.getLogger(__name__)

class ClientDataCache:
    """Thread-safe client data cache with TTL (Time To Live) functionality
    
    This cache stores client contact information and settings to reduce MongoDB queries.
    Features:
    - TTL expiration (default 5 minutes)
    - Thread-safe operations
    - Automatic cache refresh
    - Background refresh for frequently accessed clients
    - Memory-efficient storage
    """
    
    def __init__(self, ttl_minutes: int = 5):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._access_counts: Dict[str, int] = {}  # Track access frequency
        self._last_access: Dict[str, datetime] = {}  # Track last access time
        self._frequently_accessed: Set[str] = set()  # Clients accessed frequently
        self._lock = threading.RLock()
        self._ttl = timedelta(minutes=ttl_minutes)
        self._background_refresh_threshold = 5  # Access count threshold for background refresh
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache-refresh")
        logger.info(f"ClientDataCache initialized with TTL: {ttl_minutes} minutes")
    
    def _is_expired(self, client_id: str) -> bool:
        """Check if cache entry is expired"""
        if client_id not in self._timestamps:
            return True
        return datetime.now() - self._timestamps[client_id] > self._ttl
    
    def _fetch_client_data_from_db(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Fetch client data from MongoDB Atlas"""
        try:
            clients_collection = get_collection('clients')
            if not clients_collection:
                logger.error("Failed to get clients collection")
                return None
            
            # Try to find client by ObjectId first, then by custom id, domain, or api_key
            client_doc = None
            try:
                # Try ObjectId first
                client_doc = clients_collection.find_one({"_id": ObjectId(client_id)})
            except:
                pass
            
            if not client_doc:
                # Try custom id, domain, or api_key
                client_doc = clients_collection.find_one({
                    "$or": [
                        {"id": client_id},
                        {"domain": client_id},
                        {"api_key": client_id}
                    ]
                })
            
            if not client_doc:
                logger.warning(f"No client found for ID: {client_id}")
                return None
            
            # Extract and format client data
            settings = client_doc.get('settings', {})
            contact_info = settings.get('contact_info', {})
            business_hours = settings.get('business_hours', {})
            
            # Get WhatsApp number from contact_info or use phone as fallback
            whatsapp_number = contact_info.get('whatsapp', contact_info.get('phone', ''))
            
            client_data = {
                'id': client_doc.get('id', str(client_doc.get('_id', ''))),
                'status': client_doc.get('status', 'pending'),
                'business_name': client_doc.get('business_name', 'Our Business'),
                'phone': contact_info.get('phone', ''),
                'email': client_doc.get('contact_email', contact_info.get('email', '')),
                'address': contact_info.get('address', ''),
                'whatsapp': whatsapp_number,
                'business_hours': business_hours,
                'domain': client_doc.get('domain', ''),
                'average_response_time': '2-5 minutes',
                'support_hours': business_hours,
                'settings': settings,
                'cached_at': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully fetched client data from MongoDB for client_id: {client_id}")
            return client_data
            
        except Exception as e:
            logger.error(f"Error fetching client data from MongoDB: {e}")
            return None
    
    def get_client_data(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client data from cache or fetch from database if not cached/expired"""
        with self._lock:
            # Track access patterns
            self._track_access(client_id)
            
            # Check if data exists and is not expired
            if client_id in self._cache and not self._is_expired(client_id):
                logger.debug(f"Cache hit for client_id: {client_id}")
                
                # Check if we should refresh in background (proactive refresh)
                if self._should_background_refresh(client_id):
                    self._schedule_background_refresh(client_id)
                
                return self._cache[client_id].copy()
            
            # Cache miss or expired - fetch from database
            logger.debug(f"Cache miss for client_id: {client_id}, fetching from database")
            client_data = self._fetch_client_data_from_db(client_id)
            
            if client_data:
                # Store in cache
                self._cache[client_id] = client_data
                self._timestamps[client_id] = datetime.now()
                logger.info(f"Cached client data for client_id: {client_id}")
                return client_data.copy()
            
            return None
    
    def invalidate_client(self, client_id: str) -> None:
        """Invalidate cache entry for a specific client"""
        with self._lock:
            if client_id in self._cache:
                del self._cache[client_id]
                del self._timestamps[client_id]
                logger.info(f"Invalidated cache for client_id: {client_id}")
    
    def clear_cache(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            logger.info("Cleared all cache entries")
    
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
                logger.info(f"Cleaned up {len(expired_clients)} expired cache entries")
    
    def _track_access(self, client_id: str) -> None:
        """Track client access patterns for background refresh optimization"""
        now = datetime.now()
        self._access_counts[client_id] = self._access_counts.get(client_id, 0) + 1
        self._last_access[client_id] = now
        
        # Mark as frequently accessed if threshold is met
        if self._access_counts[client_id] >= self._background_refresh_threshold:
            self._frequently_accessed.add(client_id)
    
    def _should_background_refresh(self, client_id: str) -> bool:
        """Check if client data should be refreshed in background"""
        if client_id not in self._frequently_accessed:
            return False
        
        if client_id not in self._timestamps:
            return False
        
        # Refresh if 70% of TTL has passed (proactive refresh)
        time_since_cache = datetime.now() - self._timestamps[client_id]
        refresh_threshold = self._ttl * 0.7
        
        return time_since_cache > refresh_threshold
    
    def _schedule_background_refresh(self, client_id: str) -> None:
        """Schedule background refresh for a client"""
        try:
            self._executor.submit(self._background_refresh_client, client_id)
            logger.debug(f"Scheduled background refresh for client_id: {client_id}")
        except Exception as e:
            logger.error(f"Failed to schedule background refresh for {client_id}: {e}")
    
    def _background_refresh_client(self, client_id: str) -> None:
        """Refresh client data in background"""
        try:
            logger.debug(f"Background refreshing client data for: {client_id}")
            client_data = self._fetch_client_data_from_db(client_id)
            
            if client_data:
                with self._lock:
                    self._cache[client_id] = client_data
                    self._timestamps[client_id] = datetime.now()
                logger.info(f"Background refresh completed for client_id: {client_id}")
            else:
                logger.warning(f"Background refresh failed - no data found for client_id: {client_id}")
                
        except Exception as e:
            logger.error(f"Background refresh failed for client_id {client_id}: {e}")
    
    def refresh_frequently_accessed(self) -> None:
        """Refresh all frequently accessed clients in background"""
        with self._lock:
            frequently_accessed = self._frequently_accessed.copy()
        
        for client_id in frequently_accessed:
            try:
                self._executor.submit(self._background_refresh_client, client_id)
            except Exception as e:
                logger.error(f"Failed to schedule refresh for frequently accessed client {client_id}: {e}")
        
        logger.info(f"Scheduled background refresh for {len(frequently_accessed)} frequently accessed clients")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'total_entries': len(self._cache),
                'ttl_minutes': self._ttl.total_seconds() / 60,
                'cached_clients': list(self._cache.keys()),
                'frequently_accessed': list(self._frequently_accessed),
                'access_counts': dict(self._access_counts),
                'background_refresh_threshold': self._background_refresh_threshold
            }

# Global cache instance
_client_cache = None
_cache_lock = threading.Lock()

def get_client_cache() -> ClientDataCache:
    """Get the global client cache instance (singleton pattern)"""
    global _client_cache
    if _client_cache is None:
        with _cache_lock:
            if _client_cache is None:
                _client_cache = ClientDataCache(ttl_minutes=30)
    return _client_cache

def get_fallback_contact_data() -> Dict[str, Any]:
    """Fallback contact data when client data is not available"""
    return {
        'business_name': 'CleverCompanion Automotive Services',
        'phone': '+65 6123 4567',
        'email': 'support@clevercompanion.sg',
        'address': '123 Automotive Street, Singapore 123456',
        'whatsapp': '+65 6123 4567',
        'business_hours': {
            'monday': '9:00 AM - 6:00 PM',
            'tuesday': '9:00 AM - 6:00 PM',
            'wednesday': '9:00 AM - 6:00 PM',
            'thursday': '9:00 AM - 6:00 PM',
            'friday': '9:00 AM - 6:00 PM',
            'saturday': '9:00 AM - 5:00 PM',
            'sunday': 'Closed'
        },
        'domain': 'clevercompanion.sg',
        'average_response_time': '2-5 minutes',
        'support_hours': {
            'monday': '9:00 AM - 6:00 PM',
            'tuesday': '9:00 AM - 6:00 PM',
            'wednesday': '9:00 AM - 6:00 PM',
            'thursday': '9:00 AM - 6:00 PM',
            'friday': '9:00 AM - 6:00 PM',
            'saturday': '9:00 AM - 5:00 PM',
            'sunday': 'Closed'
        }
    }