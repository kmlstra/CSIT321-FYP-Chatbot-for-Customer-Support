"""Cache Warming API Routes
Provides endpoints for preloading client data into cache
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks, Depends
from typing import Optional, Dict, Any
import logging

from ..utils.cache_preloader import get_cache_preloader
from ..config.database import get_admin_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cache", tags=["cache"])

@router.post("/warm/{client_id}")
async def warm_cache_by_id(
    client_id: str,
    background_tasks: BackgroundTasks,
    db = Depends(get_admin_db)
):
    """Warm cache for a specific client by ID - called when widget initializes"""
    
    try:
        preloader = get_cache_preloader(db)
        
        # Warm cache in background for faster response
        background_tasks.add_task(preloader.preload_client_data, client_id)
        logger.info(f"Cache warming initiated for client_id: {client_id}")
        
        return {
            "success": True,
            "message": "Cache warming initiated",
            "client_id": client_id
        }
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache warming failed: {str(e)}"
        )

@router.post("/warm")
async def warm_cache(
    background_tasks: BackgroundTasks,
    client_id: Optional[str] = None,
    domain: Optional[str] = None,
    client_domain: Optional[str] = Header(None, alias="X-Client-Domain"),
    origin: Optional[str] = Header(None),
    db = Depends(get_admin_db)
):
    """Warm cache for a specific client - called when widget initializes"""
    
    try:
        # Determine client identification
        target_client_id = client_id
        target_domain = domain or client_domain
        
        # Extract domain from origin if not provided
        if not target_domain and not target_client_id and origin:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(origin)
                target_domain = parsed.netloc
            except:
                pass
        
        if not target_client_id and not target_domain:
            raise HTTPException(
                status_code=400,
                detail="Either client_id or domain must be provided"
            )
        
        preloader = get_cache_preloader(db)
        
        # Warm cache in background for faster response
        if target_client_id:
            background_tasks.add_task(preloader.preload_client_data, target_client_id)
            logger.info(f"Cache warming initiated for client_id: {target_client_id}")
        else:
            background_tasks.add_task(preloader.preload_client_by_domain, target_domain)
            logger.info(f"Cache warming initiated for domain: {target_domain}")
        
        return {
            "success": True,
            "message": "Cache warming initiated",
            "client_id": target_client_id,
            "domain": target_domain
        }
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache warming failed: {str(e)}"
        )

@router.post("/warm/sync")
async def warm_cache_sync(
    client_id: Optional[str] = None,
    domain: Optional[str] = None,
    client_domain: Optional[str] = Header(None, alias="X-Client-Domain"),
    origin: Optional[str] = Header(None),
    db = Depends(get_admin_db)
):
    """Warm cache synchronously - returns when complete"""
    
    try:
        # Determine client identification
        target_client_id = client_id
        target_domain = domain or client_domain
        
        # Extract domain from origin if not provided
        if not target_domain and not target_client_id and origin:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(origin)
                target_domain = parsed.netloc
            except:
                pass
        
        if not target_client_id and not target_domain:
            raise HTTPException(
                status_code=400,
                detail="Either client_id or domain must be provided"
            )
        
        preloader = get_cache_preloader(db)
        
        # Warm cache synchronously
        if target_client_id:
            result = await preloader.preload_client_data(target_client_id)
        else:
            result = await preloader.preload_client_by_domain(target_domain)
        
        return result
        
    except Exception as e:
        logger.error(f"Synchronous cache warming failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache warming failed: {str(e)}"
        )

@router.get("/refresh")
async def refresh_active_clients():
    """Refresh cache for frequently accessed clients in background"""
    try:
        # Use the new background refresh functionality for frequently accessed clients
        client_cache = get_client_cache()
        
        # Get current cache stats to see what we're refreshing
        cache_stats = client_cache.get_cache_stats()
        frequently_accessed = cache_stats.get('frequently_accessed', [])
        
        # Trigger background refresh for frequently accessed clients
        client_cache.refresh_frequently_accessed()
        
        return {
            "status": "success",
            "message": f"Background refresh initiated for {len(frequently_accessed)} frequently accessed clients",
            "clients_refreshed": frequently_accessed,
            "refresh_threshold": cache_stats.get('background_refresh_threshold', 5)
        }
        
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache refresh failed: {str(e)}")

@router.get("/stats")
async def get_cache_stats(db = Depends(get_admin_db)):
    """Get cache statistics"""
    
    try:
        preloader = get_cache_preloader(db)
        stats = preloader.get_cache_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}"
        )

@router.delete("/clear")
async def clear_cache(
    client_id: Optional[str] = None,
    db = Depends(get_admin_db)
):
    """Clear cache for specific client or all cache"""
    
    try:
        preloader = get_cache_preloader(db)
        
        if client_id:
            # Clear specific client cache
            cache_keys = [
                f"client_data_{client_id}",
                f"client_branding_{client_id}",
                f"client_features_{client_id}",
                f"client_contact_{client_id}",
                f"client_support_{client_id}"
            ]
            
            for key in cache_keys:
                preloader.cache.delete(key)
            
            logger.info(f"Cache cleared for client: {client_id}")
            
            return {
                "success": True,
                "message": f"Cache cleared for client: {client_id}"
            }
        else:
            # Clear all cache
            preloader.cache.clear()
            
            logger.info("All cache cleared")
            
            return {
                "success": True,
                "message": "All cache cleared"
            }
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache clear failed: {str(e)}"
        )