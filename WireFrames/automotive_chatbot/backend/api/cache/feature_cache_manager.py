"""Comprehensive Feature Cache Manager

This module provides centralized caching for all chatbot features to optimize performance
by reducing database calls for feature checks across the application.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Set, List
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from bson import ObjectId
from api.config.database import DatabaseContext


class FeatureCacheManager:
    """Centralized cache manager for all chatbot features with 1-hour TTL"""
    
    def __init__(self, ttl_seconds: int = 3600):  # 1 hour TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds
        self._access_counts: Dict[str, int] = {}
        self._last_access: Dict[str, float] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="feature_cache")
        
        # Feature defaults - used when database is unavailable or client not found
        self._feature_defaults = {
            'coe_prices': True,
            'loan_calculator': True,
            'appointment_booking': True,
            'maintenance_tips': True,
            'vehicle_search': True,
            'contact_support': True,
            'business_hours': True,
            'live_support': True,
            'custom_responses': False
        }
    
    def _is_expired(self, client_id: str) -> bool:
        """Check if cache entry is expired"""
        if client_id not in self._cache_timestamps:
            return True
        return time.time() - self._cache_timestamps[client_id] > self._ttl
    
    def _track_access(self, client_id: str):
        """Track client access for background refresh optimization"""
        current_time = time.time()
        self._access_counts[client_id] = self._access_counts.get(client_id, 0) + 1
        self._last_access[client_id] = current_time
    
    def _should_background_refresh(self, client_id: str) -> bool:
        """Determine if client should be background refreshed (70% of TTL passed)"""
        if client_id not in self._cache_timestamps:
            return False
        
        time_since_cache = time.time() - self._cache_timestamps[client_id]
        return time_since_cache > (self._ttl * 0.7)
    
    def _schedule_background_refresh(self, client_id: str):
        """Schedule background refresh for frequently accessed client"""
        if self._access_counts.get(client_id, 0) >= 3:  # Frequently accessed threshold
            self._executor.submit(self._background_refresh_client, client_id)
    
    def _background_refresh_client(self, client_id: str):
        """Background refresh client features without blocking"""
        try:
            features = self._fetch_features_from_db(client_id)
            if features:
                with self._lock:
                    self._cache[client_id] = features
                    self._cache_timestamps[client_id] = time.time()
        except Exception:
            pass  # Silent fail for background operations
    
    def _fetch_features_from_db(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Fetch client features from database"""
        try:
            with DatabaseContext('clients') as collection:
                if not collection:
                    return self._feature_defaults.copy()
                
                # Try to find client by ObjectId first (for existing clients)
                client = None
                try:
                    if ObjectId.is_valid(client_id):
                        client = collection.find_one({'_id': ObjectId(client_id)})
                except Exception:
                    pass
                
                # If not found by ObjectId, try to find by domain field (for test clients)
                if not client:
                    client = collection.find_one({'domain': client_id})
                
                # If still not found, return defaults (feature enabled by default)
                if not client:
                    return self._feature_defaults.copy()
                
                features = client.get('settings', {}).get('features', {})
                
                # Merge with defaults to ensure all features are present
                result = self._feature_defaults.copy()
                result.update(features)
                return result
                
        except Exception:
            return self._feature_defaults.copy()
    
    def get_client_features(self, client_id: str) -> Dict[str, Any]:
        """Get all features for a client with caching"""
        with self._lock:
            self._track_access(client_id)
            
            # Check if we need background refresh
            if self._should_background_refresh(client_id):
                self._schedule_background_refresh(client_id)
            
            # Return cached data if available and not expired
            if client_id in self._cache and not self._is_expired(client_id):
                return self._cache[client_id].copy()
        
        # Fetch from database
        features = self._fetch_features_from_db(client_id)
        if features:
            with self._lock:
                self._cache[client_id] = features
                self._cache_timestamps[client_id] = time.time()
            return features.copy()
        
        return self._feature_defaults.copy()
    
    def get_feature(self, client_id: str, feature_name: str) -> bool:
        """Get specific feature status for a client"""
        features = self.get_client_features(client_id)
        return features.get(feature_name, self._feature_defaults.get(feature_name, False))
    
    def get_multiple_features(self, client_id: str, feature_names: List[str]) -> Dict[str, bool]:
        """Get multiple features at once for bulk operations"""
        features = self.get_client_features(client_id)
        return {name: features.get(name, self._feature_defaults.get(name, False)) for name in feature_names}
    
    def invalidate_client(self, client_id: str):
        """Invalidate cache for specific client"""
        with self._lock:
            self._cache.pop(client_id, None)
            self._cache_timestamps.pop(client_id, None)
            self._access_counts.pop(client_id, None)
            self._last_access.pop(client_id, None)
    
    def clear_cache(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()
            self._access_counts.clear()
            self._last_access.clear()
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_clients = []
        
        with self._lock:
            for client_id, timestamp in self._cache_timestamps.items():
                if current_time - timestamp > self._ttl:
                    expired_clients.append(client_id)
            
            for client_id in expired_clients:
                self._cache.pop(client_id, None)
                self._cache_timestamps.pop(client_id, None)
                self._access_counts.pop(client_id, None)
                self._last_access.pop(client_id, None)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_time = time.time()
            active_entries = sum(1 for ts in self._cache_timestamps.values() 
                               if current_time - ts <= self._ttl)
            
            return {
                'total_entries': len(self._cache),
                'active_entries': active_entries,
                'expired_entries': len(self._cache) - active_entries,
                'ttl_seconds': self._ttl,
                'access_counts': self._access_counts.copy(),
                'frequently_accessed_clients': [
                    client_id for client_id, count in self._access_counts.items() 
                    if count >= 3
                ]
            }
    
    async def refresh_frequently_accessed(self) -> Dict[str, Any]:
        """Refresh cache for frequently accessed clients"""
        frequently_accessed = [
            client_id for client_id, count in self._access_counts.items() 
            if count >= 3
        ]
        
        refreshed_clients = []
        for client_id in frequently_accessed:
            try:
                features = self._fetch_features_from_db(client_id)
                if features:
                    with self._lock:
                        self._cache[client_id] = features
                        self._cache_timestamps[client_id] = time.time()
                    refreshed_clients.append(client_id)
            except Exception:
                continue
        
        return {
            'refreshed_clients': refreshed_clients,
            'total_frequently_accessed': len(frequently_accessed),
            'refresh_threshold': 3
        }


# Global singleton instance
_feature_cache_manager = None
_manager_lock = Lock()


def get_feature_cache_manager() -> FeatureCacheManager:
    """Get the global feature cache manager instance"""
    global _feature_cache_manager
    
    if _feature_cache_manager is None:
        with _manager_lock:
            if _feature_cache_manager is None:
                _feature_cache_manager = FeatureCacheManager()
    
    return _feature_cache_manager


# Convenience functions for common feature checks
def check_coe_feature_enabled(client_id: str) -> bool:
    """Check if COE prices feature is enabled for client"""
    return get_feature_cache_manager().get_feature(client_id, 'coe_prices')


def check_appointment_feature_enabled(client_id: str) -> bool:
    """Check if appointment booking feature is enabled for client"""
    return get_feature_cache_manager().get_feature(client_id, 'appointment_booking')


def check_live_support_feature_enabled(client_id: str) -> bool:
    """Check if live support feature is enabled for client"""
    return get_feature_cache_manager().get_feature(client_id, 'live_support')


def check_loan_calculator_feature_enabled(client_id: str) -> bool:
    """Check if loan calculator feature is enabled for client"""
    return get_feature_cache_manager().get_feature(client_id, 'loan_calculator')


def check_vehicle_search_feature_enabled(client_id: str) -> bool:
    """Check if vehicle search feature is enabled for client"""
    return get_feature_cache_manager().get_feature(client_id, 'vehicle_search')


def get_all_client_features(client_id: str) -> Dict[str, Any]:
    """Get all features for a client"""
    return get_feature_cache_manager().get_client_features(client_id)