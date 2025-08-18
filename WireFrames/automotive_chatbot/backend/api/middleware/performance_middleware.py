"""Performance Monitoring Middleware
Automatically collects performance metrics for all API requests
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..utils.performance_monitor import get_performance_monitor, record_system_error

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect performance metrics"""
    
    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/docs', '/redoc', '/openapi.json', '/favicon.ico']
        self.performance_monitor = get_performance_monitor()
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect performance metrics"""
        
        # Skip monitoring for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
            
        # Record request start time
        start_time = time.perf_counter()
        
        # Extract request information
        method = request.method
        path = request.url.path
        endpoint = f"{method} {path}"
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate response time
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000
            
            # Record performance metrics
            self.performance_monitor.record_response_time(
                endpoint=endpoint,
                response_time_ms=response_time_ms,
                status_code=response.status_code
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
            response.headers["X-Timestamp"] = str(int(time.time()))
            
            # Log slow requests
            if response_time_ms > 1000:  # Log requests slower than 1 second
                logger.warning(
                    f"Slow request detected: {endpoint} took {response_time_ms:.2f}ms"
                )
                
            return response
            
        except Exception as e:
            # Calculate response time for failed requests
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000
            
            # Record error metrics
            error_type = type(e).__name__
            record_system_error(
                error_type=error_type,
                endpoint=endpoint,
                details=str(e)
            )
            
            # Log the error
            logger.error(f"Request failed: {endpoint} - {error_type}: {str(e)}")
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "timestamp": int(time.time()),
                    "path": path
                },
                headers={
                    "X-Response-Time": f"{response_time_ms:.2f}ms",
                    "X-Error-Type": error_type
                }
            )

# Decorator for monitoring function performance
def monitor_performance(operation_type: str = "function"):
    """Decorator to monitor function performance"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                monitor = get_performance_monitor()
                monitor.record_response_time(
                    endpoint=f"{operation_type}.{func.__name__}",
                    response_time_ms=duration_ms,
                    status_code=200
                )
                
                return result
            except Exception as e:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                record_system_error(
                    error_type=type(e).__name__,
                    endpoint=f"{operation_type}.{func.__name__}",
                    details=str(e)
                )
                
                raise
                
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                monitor = get_performance_monitor()
                monitor.record_response_time(
                    endpoint=f"{operation_type}.{func.__name__}",
                    response_time_ms=duration_ms,
                    status_code=200
                )
                
                return result
            except Exception as e:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                record_system_error(
                    error_type=type(e).__name__,
                    endpoint=f"{operation_type}.{func.__name__}",
                    details=str(e)
                )
                
                raise
                
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator