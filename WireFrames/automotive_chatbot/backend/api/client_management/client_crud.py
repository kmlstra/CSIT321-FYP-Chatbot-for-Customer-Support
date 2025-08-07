"""
Client CRUD Operations - Multi-tenant SaaS Management
Handles client creation, updates, and management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import secrets
import hashlib

from ..models.client import Client, ClientUser, SUBSCRIPTION_PLANS
from ..auth.jwt_handler import create_access_token, hash_password

class ClientCRUD:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.clients_collection = database.clients
        self.users_collection = database.client_users
    
    async def create_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new client account"""
        try:
            # Validate subscription plan
            plan_type = client_data.get("subscription_plan", "basic")
            if plan_type not in SUBSCRIPTION_PLANS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid subscription plan: {plan_type}"
                )
            
            # Check if domain already exists
            existing_client = await self.clients_collection.find_one({
                "domain": client_data["domain"]
            })
            if existing_client:
                raise HTTPException(
                    status_code=400,
                    detail="Domain already registered"
                )
            
            # Generate API key
            api_key = self.generate_api_key()
            
            # Create client document
            client = Client(
                business_name=client_data["business_name"],
                domain=client_data["domain"],
                contact_email=client_data["contact_email"],
                subscription_plan=SUBSCRIPTION_PLANS[plan_type],
                status="pending",
                settings=client_data.get("settings", self.get_default_settings()),
                api_key=api_key
            )
            
            # Insert into database
            result = await self.clients_collection.insert_one(client.dict())
            client_id = str(result.inserted_id)
            
            # Create initial admin user
            admin_user_data = client_data.get("admin_user", {})
            if admin_user_data:
                await self.create_client_user(
                    client_id=client_id,
                    user_data=admin_user_data,
                    role="admin"
                )
            
            return {
                "client_id": client_id,
                "api_key": api_key,
                "status": "pending",
                "message": "Client account created successfully. Awaiting approval."
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create client: {str(e)}"
            )
    
    async def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client by ID"""
        try:
            client = await self.clients_collection.find_one({"_id": ObjectId(client_id)})
            if client:
                client["id"] = str(client["_id"])
                del client["_id"]
            return client
        except Exception:
            return None
    
    async def get_client_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get client by domain"""
        try:
            client = await self.clients_collection.find_one({"domain": domain})
            if client:
                client["id"] = str(client["_id"])
                del client["_id"]
            return client
        except Exception:
            return None
    
    async def get_client_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get client by API key"""
        try:
            client = await self.clients_collection.find_one({"api_key": api_key})
            if client:
                client["id"] = str(client["_id"])
                del client["_id"]
            return client
        except Exception:
            return None
    
    async def update_client(self, client_id: str, update_data: Dict[str, Any]) -> bool:
        """Update client configuration"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.clients_collection.update_one(
                {"_id": ObjectId(client_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update client: {str(e)}"
            )
    
    async def activate_client(self, client_id: str) -> bool:
        """Activate a pending client account"""
        try:
            result = await self.clients_collection.update_one(
                {"_id": ObjectId(client_id)},
                {
                    "$set": {
                        "status": "active",
                        "activated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to activate client: {str(e)}"
            )
    
    async def suspend_client(self, client_id: str, reason: str = "") -> bool:
        """Suspend a client account"""
        try:
            result = await self.clients_collection.update_one(
                {"_id": ObjectId(client_id)},
                {
                    "$set": {
                        "status": "suspended",
                        "suspension_reason": reason,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to suspend client: {str(e)}"
            )
    
    async def get_all_clients(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all clients, optionally filtered by status"""
        try:
            query = {}
            if status:
                query["status"] = status
            
            cursor = self.clients_collection.find(query).sort("created_at", -1)
            clients = []
            
            async for client in cursor:
                client["id"] = str(client["_id"])
                del client["_id"]
                clients.append(client)
            
            return clients
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch clients: {str(e)}"
            )
    
    async def create_client_user(self, client_id: str, user_data: Dict[str, Any], role: str = "admin") -> str:
        """Create a user for a client"""
        try:
            # Check if email already exists for this client
            existing_user = await self.users_collection.find_one({
                "client_id": client_id,
                "email": user_data["email"]
            })
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists for this client"
                )
            
            # Hash password
            password_hash = hash_password(user_data["password"])
            
            # Create user document
            user = ClientUser(
                client_id=client_id,
                email=user_data["email"],
                name=user_data["name"],
                role=role,
                password_hash=password_hash
            )
            
            # Insert into database
            result = await self.users_collection.insert_one(user.dict())
            user_id = str(result.inserted_id)
            
            return user_id
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def authenticate_client_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a client user"""
        try:
            # Find user by email
            user = await self.users_collection.find_one({"email": email})
            if not user:
                return None
            
            # Verify password
            if not self.verify_password(password, user["password_hash"]):
                return None
            
            # Check if user and client are active
            client = await self.get_client(user["client_id"])
            if not client or client["status"] != "active":
                return None
            
            # Update login info
            await self.users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {"last_login": datetime.utcnow()},
                    "$inc": {"login_count": 1}
                }
            )
            
            # Generate JWT token
            token_data = {
                "user_id": str(user["_id"]),
                "client_id": user["client_id"],
                "email": user["email"],
                "role": user["role"]
            }
            access_token = create_access_token(token_data)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": str(user["_id"]),
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "client_id": user["client_id"]
                },
                "client": client
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Authentication failed: {str(e)}"
            )
    
    async def increment_conversation_count(self, client_id: str) -> bool:
        """Increment conversation count for billing"""
        try:
            result = await self.clients_collection.update_one(
                {"_id": ObjectId(client_id)},
                {
                    "$inc": {
                        "current_month_conversations": 1,
                        "total_conversations": 1
                    },
                    "$set": {"last_activity": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception:
            return False
    
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"cc_{secrets.token_urlsafe(32)}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Get default client settings"""
        return {
            "branding": {
                "logo_url": None,
                "primary_color": "#4F46E5",
                "secondary_color": "#7C3AED",
                "company_name": "Your Automotive Business"
            },
            "features": {
                "coe_prices": True,
                "loan_calculator": True,
                "test_drive_booking": True,
                "maintenance_tips": True,
                "vehicle_search": True,
                "contact_support": True,
                "business_hours": True
            },
            "contact_info": {
                "phone": None,
                "email": None,
                "address": None,
                "whatsapp": None
            },
            "business_hours": {
                "monday": "9:00 AM - 6:00 PM",
                "tuesday": "9:00 AM - 6:00 PM",
                "wednesday": "9:00 AM - 6:00 PM",
                "thursday": "9:00 AM - 6:00 PM",
                "friday": "9:00 AM - 6:00 PM",
                "saturday": "9:00 AM - 5:00 PM",
                "sunday": "Closed"
            }
        }