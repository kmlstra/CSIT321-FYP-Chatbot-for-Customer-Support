"""
MongoDB Security Configuration for Multi-tenant SaaS
Implements Role-Based Access Control (RBAC) for client data isolation
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure
import asyncio
from typing import Dict, Any, Optional

class MongoDBSecurityManager:
    """Manages MongoDB security, roles, and client access"""
    
    def __init__(self):
        # Atlas Admin Connection (Full Access)
        self.admin_connection_string = "mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
        
        # Client Connection (Limited Access)
        self.client_connection_string = "mongodb+srv://client01:Password@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
        
        self.database_name = "automotive_chatbot_saas"
        
        # Connection pools
        self.admin_client = None
        self.client_client = None
        self.admin_db = None
        self.client_db = None
    
    async def initialize_connections(self):
        """Initialize both admin and client connections"""
        try:
            # Admin connection (full access)
            self.admin_client = AsyncIOMotorClient(self.admin_connection_string)
            self.admin_db = self.admin_client[self.database_name]
            
            # Client connection (limited access)
            self.client_client = AsyncIOMotorClient(self.client_connection_string)
            self.client_db = self.client_client[self.database_name]
            
            # Test connections
            await self.admin_client.admin.command('ping')
            await self.client_client.admin.command('ping')
            
            print("[OK] MongoDB connections established successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] MongoDB connection failed: {e}")
            return False
    
    async def setup_database_security(self):
        """Setup collections with proper security rules"""
        try:
            # Create collections with validation rules
            await self.create_secure_collections()
            
            # Setup indexes for performance and security
            await self.create_security_indexes()
            
            print("[OK] Database security setup completed")
            return True
            
        except Exception as e:
            print(f"[ERROR] Database security setup failed: {e}")
            return False
    
    async def create_secure_collections(self):
        """Create collections with validation schemas"""
        
        # Clients collection with validation
        clients_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["business_name", "domain", "contact_email", "status", "created_at"],
                "properties": {
                    "business_name": {"bsonType": "string", "minLength": 2, "maxLength": 100},
                    "domain": {"bsonType": "string", "pattern": "^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\\.[a-zA-Z]{2,}$"},
                    "contact_email": {"bsonType": "string", "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$"},
                    "status": {"enum": ["pending", "active", "suspended", "cancelled"]},
                    "api_key": {"bsonType": "string"},
                    "settings": {"bsonType": "object"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
        
        try:
            await self.admin_db.create_collection("clients", validator=clients_validator)
        except OperationFailure:
            # Collection might already exist
            pass
        
        # Client users collection
        client_users_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "email", "name", "role", "password_hash", "status"],
                "properties": {
                    "client_id": {"bsonType": "objectId"},
                    "email": {"bsonType": "string", "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$"},
                    "name": {"bsonType": "string", "minLength": 2, "maxLength": 50},
                    "role": {"enum": ["admin", "manager", "viewer"]},
                    "status": {"enum": ["pending", "active", "inactive"]},
                    "password_hash": {"bsonType": "string"}
                }
            }
        }
        
        try:
            await self.admin_db.create_collection("client_users", validator=client_users_validator)
        except OperationFailure:
            pass
        
        # Conversations collection (multi-tenant)
        conversations_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "session_id", "messages", "created_at"],
                "properties": {
                    "client_id": {"bsonType": "objectId"},
                    "session_id": {"bsonType": "string"},
                    "user_id": {"bsonType": "string"},
                    "messages": {"bsonType": "array"},
                    "total_messages": {"bsonType": "int", "minimum": 0},
                    "created_at": {"bsonType": "date"}
                }
            }
        }
        
        try:
            await self.admin_db.create_collection("conversations", validator=conversations_validator)
        except OperationFailure:
            pass
        
        # Client vehicles collection
        vehicles_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "brand", "model", "year", "price"],
                "properties": {
                    "client_id": {"bsonType": "objectId"},
                    "brand": {"bsonType": "string", "minLength": 1},
                    "model": {"bsonType": "string", "minLength": 1},
                    "year": {"bsonType": "int", "minimum": 1990, "maximum": 2030},
                    "price": {"bsonType": "number", "minimum": 0},
                    "availability": {"enum": ["in_stock", "sold", "reserved"]}
                }
            }
        }
        
        try:
            await self.admin_db.create_collection("client_vehicles", validator=vehicles_validator)
        except OperationFailure:
            pass
        
        # Analytics collection
        try:
            await self.admin_db.create_collection("analytics")
        except OperationFailure:
            pass
    
    async def create_security_indexes(self):
        """Create indexes for performance and security"""
        
        # Clients collection indexes
        await self.admin_db.clients.create_index("domain", unique=True)
        await self.admin_db.clients.create_index("api_key", unique=True)
        await self.admin_db.clients.create_index("status")
        await self.admin_db.clients.create_index("created_at")
        
        # Client users indexes
        await self.admin_db.client_users.create_index([("client_id", 1), ("email", 1)], unique=True)
        await self.admin_db.client_users.create_index("email")
        await self.admin_db.client_users.create_index("client_id")
        
        # Conversations indexes (for client data isolation)
        await self.admin_db.conversations.create_index("client_id")
        await self.admin_db.conversations.create_index([("client_id", 1), ("session_id", 1)])
        await self.admin_db.conversations.create_index("created_at")
        
        # Client vehicles indexes
        await self.admin_db.client_vehicles.create_index("client_id")
        await self.admin_db.client_vehicles.create_index([("client_id", 1), ("brand", 1), ("model", 1)])
        
        # Analytics indexes
        await self.admin_db.analytics.create_index([("client_id", 1), ("date", 1)], unique=True)
        await self.admin_db.analytics.create_index("date")
    
    def get_admin_database(self):
        """Get admin database connection (full access)"""
        return self.admin_db
    
    def get_client_database(self):
        """Get client database connection (limited access)"""
        return self.client_db
    
    async def get_client_specific_data(self, client_id: str, collection_name: str, query: Dict[str, Any] = None):
        """Get data specific to a client with automatic filtering"""
        if query is None:
            query = {}
        
        # Always filter by client_id for security
        query["client_id"] = client_id
        
        collection = self.client_db[collection_name]
        cursor = collection.find(query)
        
        results = []
        async for document in cursor:
            document["id"] = str(document["_id"])
            del document["_id"]
            results.append(document)
        
        return results
    
    async def update_client_specific_data(self, client_id: str, collection_name: str, 
                                        document_id: str, update_data: Dict[str, Any]):
        """Update data with client_id security check"""
        from bson import ObjectId
        
        collection = self.client_db[collection_name]
        
        # Security check: ensure document belongs to client
        existing_doc = await collection.find_one({
            "_id": ObjectId(document_id),
            "client_id": client_id
        })
        
        if not existing_doc:
            raise PermissionError("Document not found or access denied")
        
        # Perform update
        result = await collection.update_one(
            {"_id": ObjectId(document_id), "client_id": client_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def insert_client_data(self, client_id: str, collection_name: str, data: Dict[str, Any]):
        """Insert data with automatic client_id assignment"""
        from bson import ObjectId
        
        # Ensure client_id is set
        data["client_id"] = ObjectId(client_id) if isinstance(client_id, str) else client_id
        
        collection = self.client_db[collection_name]
        result = await collection.insert_one(data)
        
        return str(result.inserted_id)
    
    async def delete_client_data(self, client_id: str, collection_name: str, document_id: str):
        """Delete data with client_id security check"""
        from bson import ObjectId
        
        collection = self.client_db[collection_name]
        
        result = await collection.delete_one({
            "_id": ObjectId(document_id),
            "client_id": client_id
        })
        
        return result.deleted_count > 0

# Global security manager instance
security_manager = MongoDBSecurityManager()

async def get_admin_db():
    """Dependency to get admin database (for super admin operations)"""
    if not security_manager.admin_db:
        await security_manager.initialize_connections()
    return security_manager.admin_db

async def get_client_db():
    """Dependency to get client database (for client operations)"""
    if not security_manager.client_db:
        await security_manager.initialize_connections()
    return security_manager.client_db

async def get_security_manager():
    """Dependency to get security manager"""
    if not security_manager.admin_db:
        await security_manager.initialize_connections()
    return security_manager