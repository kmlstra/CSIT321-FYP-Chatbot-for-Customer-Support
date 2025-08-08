#!/usr/bin/env python3
"""
MongoDB Connectivity Checker for Automotive Chatbot Platform
This script checks MongoDB connection and provides database status
"""

import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBChecker:
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_db = os.getenv("MONGODB_DB", "chatbot_platform")
        self.client = None
        self.db = None

    async def connect(self):
        """Attempt to connect to MongoDB"""
        try:
            print("🔄 Connecting to MongoDB...")
            print(f"📍 URL: {self.mongodb_url}")
            print(f"🗄️  Database: {self.mongodb_db}")
            
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.mongodb_db]
            
            # Test the connection
            await self.client.admin.command('ping')
            print("✅ MongoDB connection successful!")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False

    async def check_database_info(self):
        """Get database information"""
        try:
            # Get server info
            server_info = await self.client.server_info()
            print(f"\n📊 MongoDB Server Info:")
            print(f"   Version: {server_info.get('version', 'Unknown')}")
            print(f"   Platform: {server_info.get('targetMinOS', 'Unknown')}")
            
            # List databases
            db_list = await self.client.list_database_names()
            print(f"\n🗃️  Available Databases: {', '.join(db_list)}")
            
            # Check if our database exists
            if self.mongodb_db in db_list:
                print(f"✅ Database '{self.mongodb_db}' exists")
                
                # List collections in our database
                collections = await self.db.list_collection_names()
                if collections:
                    print(f"📁 Collections: {', '.join(collections)}")
                else:
                    print("📁 No collections found (new database)")
            else:
                print(f"⚠️  Database '{self.mongodb_db}' does not exist yet (will be created on first write)")
                
        except Exception as e:
            print(f"❌ Error getting database info: {e}")

    async def test_operations(self):
        """Test basic database operations"""
        try:
            print(f"\n🧪 Testing basic operations...")
            
            # Test collection
            test_collection = self.db.test_connection
            
            # Insert test document
            test_doc = {
                "test": True,
                "timestamp": datetime.utcnow(),
                "message": "MongoDB connectivity test"
            }
            
            result = await test_collection.insert_one(test_doc)
            print(f"✅ Insert test: Success (ID: {result.inserted_id})")
            
            # Read test document
            found_doc = await test_collection.find_one({"test": True})
            if found_doc:
                print(f"✅ Read test: Success")
            
            # Update test document
            await test_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"updated": True}}
            )
            print(f"✅ Update test: Success")
            
            # Delete test document
            await test_collection.delete_one({"_id": result.inserted_id})
            print(f"✅ Delete test: Success")
            
            print(f"🎉 All database operations working correctly!")
            
        except Exception as e:
            print(f"❌ Database operation test failed: {e}")

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print(f"🔒 MongoDB connection closed")

async def main():
    """Main function to run MongoDB checks"""
    print("🚗 Automotive Chatbot - MongoDB Connectivity Checker")
    print("=" * 55)
    
    checker = MongoDBChecker()
    
    try:
        # Test connection
        if await checker.connect():
            await checker.check_database_info()
            await checker.test_operations()
        else:
            print(f"\n💡 Troubleshooting Tips:")
            print(f"   1. Make sure MongoDB is installed and running")
            print(f"   2. Check if MongoDB service is started:")
            print(f"      Windows: services.msc -> MongoDB Server")
            print(f"      Linux/Mac: sudo systemctl start mongod")
            print(f"   3. Verify connection string in .env file")
            print(f"   4. Check firewall settings")
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        await checker.close()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 