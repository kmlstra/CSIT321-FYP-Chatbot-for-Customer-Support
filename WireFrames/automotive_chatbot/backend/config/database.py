"""Centralized MongoDB Database Connection
Provides singleton MongoDB connection for the entire application.
"""

import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "../.env")
if Path(env_path).exists():
    load_dotenv(dotenv_path=env_path)
else:
    logger.warning("⚠️ backend/.env file not found. Database connection may fail.")

class DatabaseManager:
    """Singleton MongoDB connection manager."""
    
    _instance = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.mongodb_url = os.getenv('CHATBOT_MONGODB_URL') or os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
        self.db_name = 'automotive_chatbot_saas'  # Use existing database
        self.connection_timeout = 10000  # 10 seconds - increased timeout
        self.server_selection_timeout = 10000  # 10 seconds - increased timeout
        self._is_connected = False
        
        self._initialized = True
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection with error handling."""
        try:
            # Check if this is a MongoDB Atlas connection
            is_atlas = 'mongodb+srv://' in self.mongodb_url or 'mongodb.net' in self.mongodb_url
            
            connection_params = {
                'serverSelectionTimeoutMS': self.server_selection_timeout,
                'connectTimeoutMS': self.connection_timeout,
                'socketTimeoutMS': 30000,  # 30 seconds for socket operations
                'maxPoolSize': 5,  # Reduced connection pool size
                'minPoolSize': 1,  # Minimum pool size
                'maxIdleTimeMS': 30000,  # Close connections after 30 seconds of inactivity
                'waitQueueTimeoutMS': 10000,  # Wait 10 seconds for connection from pool
                'retryWrites': True,  # Enable retry writes
                'retryReads': True,   # Enable retry reads
            }
            
            # Add SSL/TLS configuration for Atlas connections
            if is_atlas:
                import certifi
                connection_params.update({
                    'tls': True,
                    'tlsCAFile': certifi.where(),
                    'tlsAllowInvalidHostnames': False,
                    'tlsAllowInvalidCertificates': False,
                })
            else:
                # For local MongoDB, allow invalid certificates for development
                connection_params['tlsAllowInvalidCertificates'] = True
            
            self._client = MongoClient(self.mongodb_url, **connection_params)
            
            # Test the connection
            self._client.admin.command('ping')
            self._database = self._client[self.db_name]
            self._is_connected = True
            
            logger.info(f"✅ Connected to MongoDB: {self.db_name}")
            
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            logger.warning(f"⚠️ MongoDB connection failed: {e}. Running in fallback mode.")
            self._client = None
            self._database = None
            self._is_connected = False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
            self._client = None
            self._database = None
            self._is_connected = False
    
    def get_client(self) -> Optional[MongoClient]:
        """Get MongoDB client instance."""
        if not self._is_connected:
            self._reconnect()
        return self._client
    
    def get_database(self) -> Optional[Database]:
        """Get database instance."""
        if not self._is_connected:
            self._reconnect()
        return self._database
    
    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """Get collection instance."""
        database = self.get_database()
        if database is not None:
            return database[collection_name]
        return None
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        if not self._is_connected:
            return False
            
        try:
            # Ping the database to verify connection is still alive
            if self._client:
                self._client.admin.command('ping')
                return True
        except Exception as e:
            logger.warning(f"Database connection lost: {e}")
            self._is_connected = False
            
        return False
    
    def _reconnect(self):
        """Attempt to reconnect to the database."""
        if self._is_connected:
            return
            
        logger.info("Attempting to reconnect to MongoDB...")
        self._connect()
    
    def close_connection(self):
        """Close the database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self._is_connected = False
            logger.info("MongoDB connection closed")
    
    def get_connection_info(self) -> dict:
        """Get connection information for debugging."""
        return {
            'mongodb_url': self.mongodb_url,
            'database_name': self.db_name,
            'is_connected': self._is_connected,
            'client_available': self._client is not None,
            'database_available': self._database is not None
        }

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for easy access
def get_mongodb_client() -> Optional[MongoClient]:
    """Get MongoDB client instance."""
    return db_manager.get_client()

def get_database() -> Optional[Database]:
    """Get database instance."""
    return db_manager.get_database()

def get_collection(collection_name: str) -> Optional[Collection]:
    """Get collection instance."""
    return db_manager.get_collection(collection_name)

def is_database_connected() -> bool:
    """Check if database is connected."""
    return db_manager.is_connected()

def close_database_connection():
    """Close database connection."""
    db_manager.close_connection()

def get_database_info() -> dict:
    """Get database connection information."""
    return db_manager.get_connection_info()

# Context manager for database operations
class DatabaseContext:
    """Context manager for database operations with automatic error handling."""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.collection = None
    
    def __enter__(self) -> Optional[Collection]:
        self.collection = get_collection(self.collection_name)
        if self.collection is None:
            logger.warning(f"Could not get collection '{self.collection_name}' - database not available")
        return self.collection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # No cleanup needed for MongoDB collections
        if exc_type is not None:
            logger.error(f"Error in database operation for collection '{self.collection_name}': {exc_val}")
        return False  # Don't suppress exceptions

# Example usage:
# with DatabaseContext('conversations') as collection:
#     if collection:
#         result = collection.find_one({'session_id': 'some_id'})