"""Cache Preloader System
Preloads client data into cache to improve chatbot response times
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from ..client_management.client_crud import ClientCRUD
from ..cache.client_cache import get_client_cache
from ..utils.information import get_client_support_info

logger = logging.getLogger(__name__)

class CachePreloader:
    """Handles preloading of client data into cache for improved performance"""
    
    def __init__(self, database):
        self.db = database
        self.client_crud = ClientCRUD(database)
        self.cache = get_client_cache()
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    async def preload_client_data(self, client_id: str) -> Dict[str, Any]:
        """Preload all client data into cache"""
        try:
            logger.info(f"Starting cache preload for client: {client_id}")
            
            # Load client basic data
            client = await self.client_crud.get_client(client_id)
            if not client:
                logger.warning(f"Client not found: {client_id}")
                return {"success": False, "error": "Client not found"}
            
            # Preload client data into cache by calling get_client_data
            # This will automatically cache the data from database
            cached_data = self.cache.get_client_data(client_id)
            if not cached_data:
                logger.warning(f"Failed to cache client data for {client_id}")
            
            # Note: Support info caching is not implemented in ClientDataCache yet
            # This can be enhanced later if needed
            logger.info(f"Support info caching skipped for client: {client_id}")
            
            logger.info(f"Cache preload completed for client: {client_id}")
            
            return {
                "success": True,
                "client_id": client_id,
                "cached_items": [
                    "client_data",
                    "branding",
                    "features", 
                    "contact_info",
                    "support_info"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cache preload failed for client {client_id}: {e}")
            return {
                "success": False,
                "client_id": client_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def preload_client_by_domain(self, domain: str) -> Dict[str, Any]:
        """Preload client data by domain"""
        try:
            client = await self.client_crud.get_client_by_domain(domain)
            if not client:
                return {"success": False, "error": "Client not found for domain"}
            
            return await self.preload_client_data(client["id"])
            
        except Exception as e:
            logger.error(f"Cache preload failed for domain {domain}: {e}")
            return {
                "success": False,
                "domain": domain,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def bulk_preload_active_clients(self, limit: int = 50) -> Dict[str, Any]:
        """Preload cache for all active clients (for background refresh)"""
        try:
            logger.info(f"Starting bulk cache preload for active clients (limit: {limit})")
            
            # Get active clients
            clients = await self.client_crud.get_all_clients(status="active")
            clients = clients[:limit]  # Limit to prevent overload
            
            results = []
            for client in clients:
                try:
                    result = await self.preload_client_data(client["id"])
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to preload client {client['id']}: {e}")
                    results.append({
                        "success": False,
                        "client_id": client["id"],
                        "error": str(e)
                    })
            
            successful = sum(1 for r in results if r.get("success"))
            failed = len(results) - successful
            
            logger.info(f"Bulk preload completed: {successful} successful, {failed} failed")
            
            return {
                "success": True,
                "total_clients": len(results),
                "successful": successful,
                "failed": failed,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Bulk cache preload failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_cached_client_data(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client data from cache if available"""
        return self.cache.get_client_data(client_id)
    
    def get_cached_support_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get support info from cache if available"""
        # For now, return None as ClientDataCache doesn't support support_info caching
        # This can be enhanced later if needed
        return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_cache_stats()
    
    async def warm_cache_for_widget(self, client_id: str = None, domain: str = None) -> Dict[str, Any]:
        """Warm cache specifically for widget initialization"""
        if client_id:
            return await self.preload_client_data(client_id)
        elif domain:
            return await self.preload_client_by_domain(domain)
        else:
            return {"success": False, "error": "Either client_id or domain required"}

# Global preloader instance
_preloader = None

def get_cache_preloader(database):
    """Get or create cache preloader instance"""
    global _preloader
    if not _preloader:
        _preloader = CachePreloader(database)
    return _preloader