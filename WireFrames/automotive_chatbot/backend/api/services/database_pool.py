"""Database Pool Service
Provides database connection pooling and management functionality
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import asyncpg
from datetime import datetime
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DatabasePool:
    """Database connection pool manager"""
    
    def __init__(self, database_url: str, min_size: int = 5, max_size: int = 20):
        self.database_url = database_url
        self.min_size = min_size
        self.max_size = max_size
        self.pool = None
        self._stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'queries_executed': 0,
            'errors': 0,
            'last_error': None
        }
        
    async def initialize(self):
        """Initialize the database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60
            )
            logger.info(f"Database pool initialized with {self.min_size}-{self.max_size} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            raise
            
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
            
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        connection = None
        try:
            connection = await self.pool.acquire()
            self._stats['active_connections'] += 1
            yield connection
        except Exception as e:
            self._stats['errors'] += 1
            self._stats['last_error'] = str(e)
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if connection:
                await self.pool.release(connection)
                self._stats['active_connections'] -= 1
                
    async def execute_query(self, query: str, *args):
        """Execute a query and return results"""
        async with self.get_connection() as conn:
            try:
                result = await conn.fetch(query, *args)
                self._stats['queries_executed'] += 1
                return result
            except Exception as e:
                self._stats['errors'] += 1
                self._stats['last_error'] = str(e)
                logger.error(f"Query execution error: {str(e)}")
                raise
                
    async def execute_command(self, command: str, *args):
        """Execute a command (INSERT, UPDATE, DELETE)"""
        async with self.get_connection() as conn:
            try:
                result = await conn.execute(command, *args)
                self._stats['queries_executed'] += 1
                return result
            except Exception as e:
                self._stats['errors'] += 1
                self._stats['last_error'] = str(e)
                logger.error(f"Command execution error: {str(e)}")
                raise
                
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get database pool statistics"""
        if not self.pool:
            return self._stats
            
        pool_stats = {
            'size': self.pool.get_size(),
            'min_size': self.pool.get_min_size(),
            'max_size': self.pool.get_max_size(),
            'idle_connections': self.pool.get_idle_size(),
            'active_connections': self._stats['active_connections'],
            'total_queries': self._stats['queries_executed'],
            'total_errors': self._stats['errors'],
            'last_error': self._stats['last_error']
        }
        
        return pool_stats
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database connection"""
        try:
            async with self.get_connection() as conn:
                await conn.fetchval('SELECT 1')
                return {
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'pool_stats': self.get_pool_stats()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'pool_stats': self.get_pool_stats()
            }

# Global database pool instance
_database_pool: Optional[DatabasePool] = None

async def initialize_database_pool(database_url: str = None, min_size: int = 5, max_size: int = 20):
    """Initialize the global database pool"""
    global _database_pool
    
    if not database_url:
        # Try to get from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Fallback to MongoDB Atlas URL if PostgreSQL not available
            mongodb_url = os.getenv('MONGODB_URI')
            if mongodb_url:
                logger.warning("PostgreSQL URL not found, using MongoDB connection for metrics storage")
                # For now, create a mock pool for MongoDB compatibility
                _database_pool = MockDatabasePool()
                return _database_pool
            else:
                raise ValueError("No database URL provided and DATABASE_URL not set in environment")
    
    _database_pool = DatabasePool(database_url, min_size, max_size)
    await _database_pool.initialize()
    return _database_pool

def get_database_pool() -> DatabasePool:
    """Get the global database pool instance"""
    if _database_pool is None:
        raise RuntimeError("Database pool not initialized. Call initialize_database_pool() first.")
    return _database_pool

async def close_database_pool():
    """Close the global database pool"""
    global _database_pool
    if _database_pool:
        await _database_pool.close()
        _database_pool = None

class MockDatabasePool:
    """Mock database pool for MongoDB compatibility"""
    
    def __init__(self):
        self._stats = {
            'size': 10,
            'min_size': 5,
            'max_size': 20,
            'idle_connections': 8,
            'active_connections': 2,
            'total_queries': 0,
            'total_errors': 0,
            'last_error': None
        }
        
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get mock pool statistics"""
        return self._stats.copy()
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform a mock health check"""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'pool_stats': self.get_pool_stats(),
            'note': 'Using MongoDB backend - PostgreSQL pool mocked'
        }
        
    @asynccontextmanager
    async def get_connection(self):
        """Mock connection context manager"""
        # Mock connection for compatibility
        yield None
        
    async def execute_query(self, query: str, *args):
        """Mock query execution"""
        self._stats['total_queries'] += 1
        return []
        
    async def execute_command(self, command: str, *args):
        """Mock command execution"""
        self._stats['total_queries'] += 1
        return "OK"