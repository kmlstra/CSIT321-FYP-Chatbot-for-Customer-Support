"""Database Configuration for Real MongoDB api_urlConnection"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "../../.env")
if Path(env_path).exists():
    load_dotenv(dotenv_path=env_path)

# MongoDB connection from environment variables with optimized settings
ADMIN_CONNECTION = os.getenv('CHATBOT_MONGODB_URL') or os.getenv('MONGODB_URL', 'mongodb+srv://CleverAdmin:P%40ssw0rd%211@clevercompanioncluster.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot')
DATABASE_NAME = "automotive_chatbot_saas"

# Optimized connection pool settings for faster startup
CONNECTION_POOL_SETTINGS = {
    'maxPoolSize': 20,  # Reduced max connections for faster startup
    'minPoolSize': 2,   # Reduced min connections for faster startup
    'maxIdleTimeMS': 60000,  # Increased idle time to reduce reconnections
    'serverSelectionTimeoutMS': 3000,  # Reduced timeout for faster failure detection
    'connectTimeoutMS': 5000,  # Reduced connection timeout
    'socketTimeoutMS': 10000,  # Reduced socket timeout
    'waitQueueTimeoutMS': 2000,  # Faster queue timeout
    'retryWrites': True,
    'w': 'majority'
}

# Global database connection
_admin_client: Optional[AsyncIOMotorClient] = None
_admin_db = None

async def get_real_admin_db():
    """Get real admin database connection with optimized settings"""
    global _admin_client, _admin_db
    
    if _admin_db is None:
        try:
            # Create client with optimized connection pool settings
            _admin_client = AsyncIOMotorClient(ADMIN_CONNECTION, **CONNECTION_POOL_SETTINGS)
            _admin_db = _admin_client[DATABASE_NAME]
            
            # Test connection with timeout
            await _admin_client.admin.command('ping')
            print("[OK] Connected to MongoDB Atlas with optimized connection pool")
            
        except Exception as e:
            print(f"[ERROR] Failed to connect to MongoDB: {e}")
            raise
    
    return _admin_db

# Alias for cache warming API compatibility
async def get_admin_db():
    """Alias for get_real_admin_db for cache warming API compatibility"""
    return await get_real_admin_db()

async def close_database_connection():
    """Close database connection"""
    global _admin_client
    if _admin_client:
        _admin_client.close()
        print("[INFO] Real MongoDB connection closed")

async def get_security_manager():
    """Get security manager instance"""
    # Import here to avoid circular imports
    from ..config.mongodb_security import get_security_manager as get_real_security_manager
    return await get_real_security_manager()

class DatabaseContext:
    """Database context manager for both sync and async operations"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._db = None
        self._collection = None
        self._sync_client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            self._db = await get_real_admin_db()
            self._collection = self._db[self.collection_name]
            return self._collection
        except Exception as e:
            print(f"[ERROR] Failed to enter async context: {e}")
            return None
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Connection cleanup is handled globally
        pass
    
    def __enter__(self):
        """Sync context manager entry"""
        import pymongo
        try:
            # Use separate connection for sync operations to avoid event loop conflicts
            self._sync_client = pymongo.MongoClient(
                ADMIN_CONNECTION,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000
            )
            self._db = self._sync_client[DATABASE_NAME]
            self._collection = self._db[self.collection_name]
            return self._collection
        except Exception as e:
            print(f"[ERROR] Failed to enter sync context: {e}")
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit"""
        if self._sync_client:
            try:
                self._sync_client.close()
            except Exception as e:
                print(f"[WARNING] Error closing sync client: {e}")
            finally:
                self._sync_client = None
    
    def get_sync_collection(self):
        """Get collection for synchronous operations (for RASA actions)"""
        import asyncio
        import pymongo
        
        try:
            # Use pymongo for sync operations to avoid event loop issues
            sync_client = pymongo.MongoClient(ADMIN_CONNECTION)
            sync_db = sync_client[DATABASE_NAME]
            return sync_db[self.collection_name]
        except Exception as e:
            print(f"[ERROR] Failed to get sync collection: {e}")
            return None

# Convenience function for getting collections synchronously
def get_collection(collection_name: str):
    """Get MongoDB collection synchronously (for RASA actions)"""
    context = DatabaseContext(collection_name)
    return context.get_sync_collection()

# Check if database is connected (sync version)
def is_database_connected() -> bool:
    """Check if database is connected (synchronous)"""
    import pymongo
    try:
        client = pymongo.MongoClient(ADMIN_CONNECTION, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        client.close()
        return True
    except Exception:
        return False