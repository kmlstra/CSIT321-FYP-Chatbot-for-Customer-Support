"""\nHealth Check Routes\nProvides comprehensive system health monitoring endpoints\n"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..utils.performance_monitor import get_performance_monitor, get_health_summary
from ..utils.health_monitor import HealthMonitor
from ..services.database_pool import get_database_pool
from ..services.cache_service import get_cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

# Initialize health monitor
health_monitor = HealthMonitor()

@router.get("/")
async def basic_health_check():
    """Basic health check endpoint"""
    try:
        # Quick system check
        current_time = datetime.utcnow()
        
        return {
            "status": "healthy",
            "timestamp": current_time.isoformat(),
            "uptime": "available",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@router.get("/detailed")
async def detailed_health_check():
    """Comprehensive health check with all system components"""
    try:
        # Get performance monitor
        perf_monitor = get_performance_monitor()
        
        # Check all services
        services_status = await health_monitor.monitor_all_services()
        
        # Get system resources
        system_resources = health_monitor.check_system_resources()
        
        # Get performance summary
        performance_summary = get_health_summary()
        
        # Check database connection
        db_status = await check_database_health()
        
        # Check cache service
        cache_status = await check_cache_health()
        
        # Calculate overall health score
        health_score = calculate_health_score(services_status, system_resources)
        
        return {
            "status": "healthy" if health_score > 0.8 else "degraded" if health_score > 0.5 else "unhealthy",
            "health_score": health_score,
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status,
            "system_resources": system_resources,
            "performance": performance_summary,
            "database": db_status,
            "cache": cache_status,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/services")
async def services_health_check():
    """Check health of all external services"""
    try:
        services_status = await health_monitor.monitor_all_services()
        
        # Count healthy services
        total_services = len(services_status)
        healthy_services = sum(1 for service in services_status.values() if service.get('status') == 'healthy')
        
        overall_status = "healthy" if healthy_services == total_services else "degraded" if healthy_services > 0 else "unhealthy"
        
        return {
            "status": overall_status,
            "healthy_services": healthy_services,
            "total_services": total_services,
            "services": services_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Services health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Services check failed: {str(e)}")

@router.get("/performance")
async def performance_health_check():
    """Get current performance metrics and health status"""
    try:
        perf_monitor = get_performance_monitor()
        
        # Get performance summary
        performance_data = get_health_summary()
        
        # Get recent metrics (last 5 minutes)
        recent_metrics = perf_monitor.get_recent_metrics(minutes=5)
        
        # Calculate performance health score
        perf_score = calculate_performance_score(performance_data)
        
        return {
            "status": "healthy" if perf_score > 0.8 else "degraded" if perf_score > 0.5 else "poor",
            "performance_score": perf_score,
            "summary": performance_data,
            "recent_metrics": recent_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Performance check failed: {str(e)}")

@router.get("/database")
async def database_health_check():
    """Check database connection and performance"""
    try:
        db_status = await check_database_health()
        
        return {
            "status": db_status["status"],
            "details": db_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database check failed: {str(e)}")

@router.get("/cache")
async def cache_health_check():
    """Check cache service health and performance"""
    try:
        cache_status = await check_cache_health()
        
        return {
            "status": cache_status["status"],
            "details": cache_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Cache check failed: {str(e)}")

@router.get("/alerts")
async def get_active_alerts():
    """Get current system alerts and warnings"""
    try:
        perf_monitor = get_performance_monitor()
        
        # Get recent alerts
        alerts = perf_monitor.get_active_alerts()
        
        # Categorize alerts by severity
        critical_alerts = [alert for alert in alerts if alert.get('severity') == 'critical']
        warning_alerts = [alert for alert in alerts if alert.get('severity') == 'warning']
        info_alerts = [alert for alert in alerts if alert.get('severity') == 'info']
        
        return {
            "total_alerts": len(alerts),
            "critical": len(critical_alerts),
            "warnings": len(warning_alerts),
            "info": len(info_alerts),
            "alerts": {
                "critical": critical_alerts,
                "warnings": warning_alerts,
                "info": info_alerts
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Alerts check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Alerts check failed: {str(e)}")

# Helper functions

async def check_database_health() -> Dict[str, Any]:
    """Check database connection and performance"""
    try:
        db_pool = get_database_pool()
        start_time = time.perf_counter()
        
        # Test database connection
        db = await db_pool.get_database()
        
        # Simple ping test
        await db.command('ping')
        
        end_time = time.perf_counter()
        response_time = (end_time - start_time) * 1000
        
        # Get connection pool stats
        pool_stats = db_pool.get_pool_stats()
        
        return {
            "status": "healthy" if response_time < 100 else "slow",
            "response_time_ms": round(response_time, 2),
            "pool_stats": pool_stats,
            "connection_string": "mongodb+srv://***:***@cluster.mongodb.net/***"
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": None
        }

async def check_cache_health() -> Dict[str, Any]:
    """Check cache service health and performance"""
    try:
        cache_service = get_cache_service()
        start_time = time.perf_counter()
        
        # Test cache with a simple operation
        test_key = "health_check_test"
        test_value = {"timestamp": time.time()}
        
        # Set and get test value
        await cache_service.set(test_key, test_value, ttl=60)
        retrieved_value = await cache_service.get(test_key)
        
        end_time = time.perf_counter()
        response_time = (end_time - start_time) * 1000
        
        # Clean up test key
        await cache_service.delete(test_key)
        
        # Get cache stats
        cache_stats = await cache_service.get_stats()
        
        return {
            "status": "healthy" if response_time < 50 and retrieved_value else "degraded",
            "response_time_ms": round(response_time, 2),
            "test_successful": retrieved_value is not None,
            "stats": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": None
        }

def calculate_health_score(services_status: Dict, system_resources: Dict) -> float:
    """Calculate overall system health score (0.0 to 1.0)"""
    try:
        # Service health weight: 40%
        total_services = len(services_status)
        healthy_services = sum(1 for service in services_status.values() if service.get('status') == 'healthy')
        service_score = healthy_services / total_services if total_services > 0 else 0
        
        # System resources weight: 60%
        cpu_score = max(0, (100 - system_resources.get('cpu_percent', 100)) / 100)
        memory_score = max(0, (100 - system_resources.get('memory_percent', 100)) / 100)
        disk_score = max(0, (100 - system_resources.get('disk_percent', 100)) / 100)
        
        resource_score = (cpu_score + memory_score + disk_score) / 3
        
        # Calculate weighted score
        overall_score = (service_score * 0.4) + (resource_score * 0.6)
        
        return round(overall_score, 3)
        
    except Exception as e:
        logger.error(f"Health score calculation failed: {str(e)}")
        return 0.0

def calculate_performance_score(performance_data: Dict) -> float:
    """Calculate performance health score based on metrics"""
    try:
        # Default score
        score = 1.0
        
        # Check average response time (target: < 500ms)
        avg_response_time = performance_data.get('avg_response_time_ms', 0)
        if avg_response_time > 1000:
            score -= 0.3
        elif avg_response_time > 500:
            score -= 0.1
            
        # Check error rate (target: < 1%)
        error_rate = performance_data.get('error_rate_percent', 0)
        if error_rate > 5:
            score -= 0.4
        elif error_rate > 1:
            score -= 0.2
            
        # Check active connections (reasonable limits)
        active_connections = performance_data.get('active_connections', 0)
        if active_connections > 1000:
            score -= 0.2
        elif active_connections > 500:
            score -= 0.1
            
        return max(0.0, round(score, 3))
        
    except Exception as e:
        logger.error(f"Performance score calculation failed: {str(e)}")
        return 0.0