"""MongoDB Security Configuration"""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime

class SecurityManager:
    """Security manager for client data access control"""
    
    def __init__(self, database):
        self.db = database
    
    async def get_client_specific_data(self, client_id: str, collection_name: str) -> List[Dict[str, Any]]:
        """Get client-specific data from a collection"""
        try:
            if collection_name == "client_vehicles":
                # Get vehicles for this client
                cursor = self.db.client_vehicles.find({"client_id": client_id})
                vehicles = await cursor.to_list(length=100)
                # Convert ObjectId to string for JSON serialization
                for vehicle in vehicles:
                    if "_id" in vehicle:
                        vehicle["_id"] = str(vehicle["_id"])
                return vehicles
            elif collection_name == "conversations":
                # Get conversations for this client, sorted by created_at (latest first)
                cursor = self.db.conversations.find({"client_id": client_id}).sort("created_at", -1)
                conversations = await cursor.to_list(length=100)
                # Convert ObjectId to string for JSON serialization
                for conv in conversations:
                    if "_id" in conv:
                        conv["_id"] = str(conv["_id"])
                return conversations
            else:
                # Generic collection access
                cursor = self.db[collection_name].find({"client_id": client_id})
                data = await cursor.to_list(length=100)
                # Convert ObjectId to string for JSON serialization
                for item in data:
                    if "_id" in item:
                        item["_id"] = str(item["_id"])
                return data
        except Exception as e:
            print(f"[ERROR] SecurityManager.get_client_specific_data: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def insert_client_data(self, client_id: str, collection_name: str, data: Dict[str, Any]) -> str:
        """Insert client-specific data into a collection"""
        try:
            data["client_id"] = client_id
            data["_id"] = ObjectId()
            result = await self.db[collection_name].insert_one(data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"[ERROR] SecurityManager.insert_client_data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_client_specific_data(self, client_id: str, collection_name: str, 
                                        item_id: str, update_data: Dict[str, Any]) -> bool:
        """Update client-specific data in a collection"""
        try:
            result = await self.db[collection_name].update_one(
                {"_id": ObjectId(item_id), "client_id": client_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"[ERROR] SecurityManager.update_client_specific_data: {e}")
            return False
    
    async def delete_client_data(self, client_id: str, collection_name: str, item_id: str) -> bool:
        """Delete client-specific data from a collection"""
        try:
            result = await self.db[collection_name].delete_one(
                {"_id": ObjectId(item_id), "client_id": client_id}
            )
            return result.deleted_count > 0
        except Exception as e:
            print(f"[ERROR] SecurityManager.delete_client_data: {e}")
            return False

# Global security manager instance
_security_manager = None

async def get_security_manager():
    """Get security manager instance"""
    global _security_manager
    if _security_manager is None:
        # Use the new database connection method
        try:
            from .database import get_real_admin_db
            db = await get_real_admin_db()
            if db is not None:
                _security_manager = SecurityManager(db)
            else:
                # Fallback to creating a new connection
                from motor.motor_asyncio import AsyncIOMotorClient
                ADMIN_CONNECTION = "mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
                DATABASE_NAME = "automotive_chatbot_saas"
                client = AsyncIOMotorClient(ADMIN_CONNECTION)
                db = client[DATABASE_NAME]
                _security_manager = SecurityManager(db)
        except Exception as e:
            # Fallback to creating a new connection
            from motor.motor_asyncio import AsyncIOMotorClient
            ADMIN_CONNECTION = "mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
            DATABASE_NAME = "automotive_chatbot_saas"
            client = AsyncIOMotorClient(ADMIN_CONNECTION)
            db = client[DATABASE_NAME]
            _security_manager = SecurityManager(db)
    return _security_manager