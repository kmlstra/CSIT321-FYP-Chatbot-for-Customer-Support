#!/usr/bin/env python3
"""
Cache Management Utility
Provides functions to manage the client data cache
"""

import logging
from typing import List, Dict, Any
from .client_cache import get_client_cache

logger = logging.getLogger(__name__)

def invalidate_client_cache(client_id: str) -> bool:
    """Invalidate cache for a specific client
    
    Args:
        client_id: The client ID to invalidate
        
    Returns:
        bool: True if cache was invalidated, False if client was not cached
    """
    try:
        cache = get_client_cache()
        cache.invalidate_client(client_id)
        logger.info(f"Cache invalidated for client_id: {client_id}")
        return True
    except Exception as e:
        logger.error(f"Error invalidating cache for client_id {client_id}: {e}")
        return False

def refresh_client_cache(client_id: str) -> bool:
    """Refresh cache for a specific client by invalidating and re-fetching
    
    Args:
        client_id: The client ID to refresh
        
    Returns:
        bool: True if cache was refreshed successfully
    """
    try:
        cache = get_client_cache()
        # Invalidate existing cache
        cache.invalidate_client(client_id)
        # Fetch fresh data (this will cache it)
        fresh_data = cache.get_client_data(client_id)
        if fresh_data:
            logger.info(f"Cache refreshed for client_id: {client_id}")
            return True
        else:
            logger.warning(f"No data found when refreshing cache for client_id: {client_id}")
            return False
    except Exception as e:
        logger.error(f"Error refreshing cache for client_id {client_id}: {e}")
        return False

def clear_all_cache() -> bool:
    """Clear all cached client data
    
    Returns:
        bool: True if cache was cleared successfully
    """
    try:
        cache = get_client_cache()
        cache.clear_cache()
        logger.info("All cache cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False

def cleanup_expired_cache() -> bool:
    """Remove expired entries from cache
    
    Returns:
        bool: True if cleanup was successful
    """
    try:
        cache = get_client_cache()
        cache.cleanup_expired()
        logger.info("Expired cache entries cleaned up")
        return True
    except Exception as e:
        logger.error(f"Error cleaning up expired cache: {e}")
        return False

def get_cache_info() -> Dict[str, Any]:
    """Get current cache information and statistics
    
    Returns:
        dict: Cache statistics and information
    """
    try:
        cache = get_client_cache()
        stats = cache.get_cache_stats()
        return {
            'status': 'active',
            'total_entries': stats['total_entries'],
            'ttl_minutes': stats['ttl_minutes'],
            'cached_clients': stats['cached_clients']
        }
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

def bulk_invalidate_clients(client_ids: List[str]) -> Dict[str, bool]:
    """Invalidate cache for multiple clients
    
    Args:
        client_ids: List of client IDs to invalidate
        
    Returns:
        dict: Results for each client ID
    """
    results = {}
    for client_id in client_ids:
        results[client_id] = invalidate_client_cache(client_id)
    return results

def bulk_refresh_clients(client_ids: List[str]) -> Dict[str, bool]:
    """Refresh cache for multiple clients
    
    Args:
        client_ids: List of client IDs to refresh
        
    Returns:
        dict: Results for each client ID
    """
    results = {}
    for client_id in client_ids:
        results[client_id] = refresh_client_cache(client_id)
    return results

# Convenience functions for common operations
def on_client_data_updated(client_id: str) -> bool:
    """Call this function when client data is updated in the database
    to ensure cache consistency
    
    Args:
        client_id: The client ID that was updated
        
    Returns:
        bool: True if cache was refreshed successfully
    """
    return refresh_client_cache(client_id)

def on_client_deleted(client_id: str) -> bool:
    """Call this function when a client is deleted from the database
    to remove it from cache
    
    Args:
        client_id: The client ID that was deleted
        
    Returns:
        bool: True if cache was invalidated successfully
    """
    return invalidate_client_cache(client_id)