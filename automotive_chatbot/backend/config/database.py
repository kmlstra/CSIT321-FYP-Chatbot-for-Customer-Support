"""
MongoDB Database Configuration
This module handles MongoDB connection and configuration
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv
import asyncio
from datetime import datetime

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """MongoDB database configuration and connection management"""
    
    def __init__(self):
        # MongoDB Configuration from environment variables
        self.MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.MONGODB_DB = os.getenv("MONGODB_DB", "chatbot_platform")
        self.CONNECTION_TIMEOUT = int(os.getenv("MONGODB_TIMEOUT", "5000"))
        
        # Client instances
        self.client = None
        self.database = None
        
    async def connect(self) -> bool:
        """
        Establish connection to MongoDB
        Returns True if successful, False otherwise
        """
        try:
            print(f"🔄 Connecting to MongoDB...")
            print(f"📍 URL: {self.MONGODB_URL}")
            print(f"🗄️  Database: {self.MONGODB_DB}")
            
            # Create client
            self.client = AsyncIOMotorClient(
                self.MONGODB_URL,
                serverSelectionTimeoutMS=self.CONNECTION_TIMEOUT
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Get database
            self.database = self.client[self.MONGODB_DB]
            
            print("✅ MongoDB connection established successfully!")
            return True
            
        except ServerSelectionTimeoutError:
            print("❌ MongoDB connection timeout - server not reachable")
            return False
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("🔒 MongoDB connection closed")
    
    async def health_check(self) -> dict:
        """
        Perform MongoDB health check
        Returns health status information
        """
        try:
            # Server info
            server_info = await self.client.server_info()
            
            # Database stats
            db_stats = await self.database.command("dbStats")
            
            # Collections
            collections = await self.database.list_collection_names()
            
            return {
                "status": "healthy",
                "server_version": server_info.get("version", "unknown"),
                "database": self.MONGODB_DB,
                "collections": collections,
                "database_size": db_stats.get("dataSize", 0),
                "collections_count": len(collections),
                "connection_url": self.MONGODB_URL.replace(
                    self.MONGODB_URL.split('@')[0].split('//')[1] + '@', '***:***@'
                ) if '@' in self.MONGODB_URL else self.MONGODB_URL
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": self.MONGODB_DB,
                "connection_url": self.MONGODB_URL
            }
    
    def get_collection(self, collection_name: str):
        """Get a specific collection"""
        if not self.database:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.database[collection_name]

# Global database instance
db_config = DatabaseConfig()

async def get_database():
    """Dependency to get database instance"""
    if not db_config.database:
        await db_config.connect()
    return db_config.database

# Collections shortcuts
async def get_users_collection():
    """Get users collection"""
    db = await get_database()
    return db.users

async def get_chatbots_collection():
    """Get chatbots collection"""
    db = await get_database()
    return db.chatbots

async def get_conversations_collection():
    """Get conversations collection"""
    db = await get_database()
    return db.conversations

async def get_analytics_collection():
    """Get analytics collection"""
    db = await get_database()
    return db.analytics 