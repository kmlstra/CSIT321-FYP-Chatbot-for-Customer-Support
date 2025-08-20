"""Database Connection Pool Manager
Provides efficient MongoDB connection pooling for improved performance
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from dotenv import load_dotenv
from pathlib import Path
import time
from threading import Lock

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Configure logging
logger = logging.getLogger('api.utils.database_pool')
logger.setLevel(logging.DEBUG)

class DatabasePool:
    """MongoDB connection pool manager with async support
    
    Features:
    - Connection pooling for improved performance
    - Automatic connection health checks
    - Retry logic for failed connections
    - Thread-safe singleton pattern
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabasePool, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the database pool"""
        if self._initialized:
            return
            
        self.mongodb_url = os.getenv('MONGODB_URL')
        self.database_name = os.getenv('DATABASE_NAME', 'automotive_chatbot_saas')
        
        # Connection pool settings - 优化超时设置
        self.max_pool_size = int(os.getenv('MONGODB_MAX_POOL_SIZE', '10'))  # 减少连接池大小
        self.min_pool_size = int(os.getenv('MONGODB_MIN_POOL_SIZE', '2'))
        self.max_idle_time_ms = int(os.getenv('MONGODB_MAX_IDLE_TIME_MS', '10000'))  # 减少空闲时间
        self.connect_timeout_ms = int(os.getenv('MONGODB_CONNECT_TIMEOUT_MS', '3000'))  # 减少连接超时
        self.server_selection_timeout_ms = int(os.getenv('MONGODB_SERVER_SELECTION_TIMEOUT_MS', '3000'))  # 减少服务器选择超时
        
        # Connection state
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        self._connection_retries = 3
        self._retry_delay = 1  # seconds
        
        self._initialized = True
        logger.info("DatabasePool initialized with connection pooling")
    
    async def _create_client(self) -> AsyncIOMotorClient:
        """Create a new MongoDB client with optimized settings"""
        if not self.mongodb_url:
            raise ValueError("MONGODB_URL environment variable is not set")
        
        client_options = {
            'maxPoolSize': self.max_pool_size,
            'minPoolSize': self.min_pool_size,
            'maxIdleTimeMS': self.max_idle_time_ms,
            'connectTimeoutMS': self.connect_timeout_ms,
            'serverSelectionTimeoutMS': self.server_selection_timeout_ms,
            'retryWrites': True,
            'retryReads': True,
            'w': 'majority',
            'readPreference': 'primaryPreferred',
            'compressors': ['zstd', 'zlib', 'snappy'],
            'zlibCompressionLevel': 6
        }
        
        logger.debug(f"Creating MongoDB client with options: {client_options}")
        client = AsyncIOMotorClient(self.mongodb_url, **client_options)
        
        # Test the connection
        try:
            await client.admin.command('ping')
            logger.info("MongoDB connection established successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to establish MongoDB connection: {e}")
            await client.close()
            raise
    
    async def _health_check(self) -> bool:
        """Perform health check on the database connection"""
        if not self._client or not self._database:
            return False
        
        try:
            # Simple ping to check connection health
            await self._client.admin.command('ping')
            self._last_health_check = time.time()
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False
    
    async def _ensure_connection(self) -> bool:
        """Ensure database connection is healthy"""
        current_time = time.time()
        
        # Check if we need to perform health check
        if (current_time - self._last_health_check) > self._health_check_interval:
            if not await self._health_check():
                logger.info("Health check failed, reconnecting...")
                await self._reconnect()
        
        return self._client is not None and self._database is not None
    
    async def _reconnect(self) -> None:
        """Reconnect to the database with retry logic"""
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.warning(f"Error closing existing client: {e}")
        
        self._client = None
        self._database = None
        
        for attempt in range(self._connection_retries):
            try:
                logger.info(f"Attempting to reconnect to MongoDB (attempt {attempt + 1}/{self._connection_retries})")
                self._client = await self._create_client()
                self._database = self._client[self.database_name]
                logger.info("Successfully reconnected to MongoDB")
                return
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
                if attempt < self._connection_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
        
        logger.error("Failed to reconnect to MongoDB after all attempts")
    
    async def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        """Get database connection with automatic reconnection"""
        try:
            # Initialize connection if not exists
            if not self._client or not self._database:
                await self._reconnect()
            
            # Ensure connection is healthy
            if not await self._ensure_connection():
                logger.error("Failed to ensure database connection")
                return None
            
            return self._database
        
        except Exception as e:
            logger.error(f"Error getting database connection: {e}")
            return None
    
    async def get_collection(self, collection_name: str):
        """Get a specific collection from the database"""
        database = await self.get_database()
        if database is None:
            return None
        return database[collection_name]
    
    async def close(self) -> None:
        """Close the database connection"""
        if self._client:
            try:
                await self._client.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._client = None
                self._database = None
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self._client:
            return {'status': 'disconnected'}
        
        try:
            # Get connection pool stats from the client
            pool_stats = {
                'status': 'connected',
                'database_name': self.database_name,
                'max_pool_size': self.max_pool_size,
                'min_pool_size': self.min_pool_size,
                'last_health_check': self._last_health_check,
                'health_check_interval': self._health_check_interval
            }
            
            return pool_stats
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            return {'status': 'error', 'error': str(e)}

# Global database pool instance
_db_pool = None

def get_database_pool() -> DatabasePool:
    """Get the global database pool instance"""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool()
    return _db_pool

# Convenience functions for backward compatibility
async def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Get database connection using the global pool"""
    pool = get_database_pool()
    return await pool.get_database()

async def get_collection(collection_name: str):
    """Get collection using the global pool"""
    pool = get_database_pool()
    return await pool.get_collection(collection_name)