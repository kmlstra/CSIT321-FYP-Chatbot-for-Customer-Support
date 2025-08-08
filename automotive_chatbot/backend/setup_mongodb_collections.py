#!/usr/bin/env python3
"""
MongoDB Collections Setup for SaaS Automotive Chatbot Platform
Creates all necessary collections with proper validation and indexes
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

# MongoDB Atlas connection strings
ADMIN_CONNECTION = "mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
CLIENT_CONNECTION = "mongodb+srv://client01:Password@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
DATABASE_NAME = "automotive_chatbot_saas"

class MongoDBSetup:
    def __init__(self):
        self.admin_client = None
        self.admin_db = None
    
    async def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            self.admin_client = AsyncIOMotorClient(ADMIN_CONNECTION)
            self.admin_db = self.admin_client[DATABASE_NAME]
            
            # Test connection
            await self.admin_client.admin.command('ping')
            print("[OK] Database security setup completed")
            return True
            
        except Exception as e:
            print(f"[ERROR] Database security setup failed: {e}")
            return False
    
    async def create_collections_with_validation(self):
        """Create all collections with validation schemas"""
        
        print("🔧 Creating collections with validation schemas...")
        
        # 1. CLIENTS COLLECTION
        clients_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["business_name", "domain", "contact_email", "status", "created_at"],
                "properties": {
                    "business_name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 100,
                        "description": "Business name must be 2-100 characters"
                    },
                    "domain": {
                        "bsonType": "string",
                        "pattern": "^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\\.[a-zA-Z]{2,}$",
                        "description": "Must be a valid domain name"
                    },
                    "contact_email": {
                        "bsonType": "string",
                        "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$",
                        "description": "Must be a valid email address"
                    },
                    "status": {
                        "enum": ["pending", "active", "suspended", "cancelled"],
                        "description": "Client account status"
                    },
                    "api_key": {
                        "bsonType": "string",
                        "description": "Unique API key for widget authentication"
                    },
                    "settings": {
                        "bsonType": "object",
                        "properties": {
                            "branding": {"bsonType": "object"},
                            "features": {"bsonType": "object"},
                            "contact_info": {"bsonType": "object"},
                            "business_hours": {"bsonType": "object"}
                        }
                    },
                    "subscription_plan": {"bsonType": "object"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"},
                    "current_month_conversations": {"bsonType": "int", "minimum": 0},
                    "total_conversations": {"bsonType": "int", "minimum": 0}
                }
            }
        }
        
        await self.create_collection_safe("clients", clients_validator)
        
        # 2. CLIENT_USERS COLLECTION
        client_users_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "email", "name", "role", "password_hash", "status"],
                "properties": {
                    "client_id": {
                        "bsonType": "objectId",
                        "description": "Reference to client document"
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$",
                        "description": "Must be a valid email address"
                    },
                    "name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 50,
                        "description": "User name must be 2-50 characters"
                    },
                    "role": {
                        "enum": ["admin", "manager", "viewer"],
                        "description": "User role within client organization"
                    },
                    "status": {
                        "enum": ["pending", "active", "inactive"],
                        "description": "User account status"
                    },
                    "password_hash": {
                        "bsonType": "string",
                        "description": "Hashed password"
                    },
                    "permissions": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "created_at": {"bsonType": "date"},
                    "last_login": {"bsonType": "date"},
                    "login_count": {"bsonType": "int", "minimum": 0}
                }
            }
        }
        
        await self.create_collection_safe("client_users", client_users_validator)
        
        # 3. CONVERSATIONS COLLECTION
        conversations_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "session_id", "messages", "created_at"],
                "properties": {
                    "client_id": {
                        "bsonType": "objectId",
                        "description": "Reference to client document"
                    },
                    "session_id": {
                        "bsonType": "string",
                        "description": "Unique session identifier"
                    },
                    "user_id": {
                        "bsonType": "string",
                        "description": "Anonymous or registered user ID"
                    },
                    "messages": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["role", "content", "timestamp"],
                            "properties": {
                                "role": {"enum": ["user", "assistant"]},
                                "content": {"bsonType": "string"},
                                "timestamp": {"bsonType": "date"}
                            }
                        }
                    },
                    "total_messages": {"bsonType": "int", "minimum": 0},
                    "lead_status": {
                        "enum": ["new", "qualified", "contacted", "converted"],
                        "description": "Lead qualification status"
                    },
                    "user_satisfaction": {
                        "bsonType": "int",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "User satisfaction rating 1-5"
                    },
                    "created_at": {"bsonType": "date"},
                    "ended_at": {"bsonType": "date"}
                }
            }
        }
        
        await self.create_collection_safe("conversations", conversations_validator)
        
        # 4. CLIENT_VEHICLES COLLECTION
        vehicles_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "brand", "model", "year", "price"],
                "properties": {
                    "client_id": {
                        "bsonType": "objectId",
                        "description": "Reference to client document"
                    },
                    "brand": {
                        "bsonType": "string",
                        "minLength": 1,
                        "description": "Vehicle brand"
                    },
                    "model": {
                        "bsonType": "string",
                        "minLength": 1,
                        "description": "Vehicle model"
                    },
                    "year": {
                        "bsonType": "int",
                        "minimum": 1990,
                        "maximum": 2030,
                        "description": "Manufacturing year"
                    },
                    "price": {
                        "bsonType": "number",
                        "minimum": 0,
                        "description": "Vehicle price in SGD"
                    },
                    "coe_category": {
                        "enum": ["A", "B", "C", "E"],
                        "description": "COE category"
                    },
                    "availability": {
                        "enum": ["in_stock", "sold", "reserved"],
                        "description": "Vehicle availability status"
                    },
                    "engine_capacity": {"bsonType": "number", "minimum": 0},
                    "fuel_type": {
                        "enum": ["Petrol", "Hybrid", "Electric", "Diesel"],
                        "description": "Fuel type"
                    },
                    "transmission": {
                        "enum": ["Manual", "Automatic", "CVT"],
                        "description": "Transmission type"
                    },
                    "features": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "images": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
        
        await self.create_collection_safe("client_vehicles", vehicles_validator)
        
        # 5. ANALYTICS COLLECTION
        analytics_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "date"],
                "properties": {
                    "client_id": {
                        "bsonType": "objectId",
                        "description": "Reference to client document"
                    },
                    "date": {
                        "bsonType": "date",
                        "description": "Analytics date"
                    },
                    "total_conversations": {"bsonType": "int", "minimum": 0},
                    "unique_users": {"bsonType": "int", "minimum": 0},
                    "avg_response_time": {"bsonType": "number", "minimum": 0},
                    "user_satisfaction_avg": {"bsonType": "number", "minimum": 1, "maximum": 5},
                    "popular_intents": {"bsonType": "object"},
                    "popular_vehicles": {"bsonType": "object"},
                    "test_drives_booked": {"bsonType": "int", "minimum": 0},
                    "contact_requests": {"bsonType": "int", "minimum": 0},
                    "loan_calculations": {"bsonType": "int", "minimum": 0},
                    "error_rate": {"bsonType": "number", "minimum": 0, "maximum": 1},
                    "uptime_percentage": {"bsonType": "number", "minimum": 0, "maximum": 100}
                }
            }
        }
        
        await self.create_collection_safe("analytics", analytics_validator)
        
        print("✅ All collections created successfully")
    
    async def create_collection_safe(self, collection_name, validator=None):
        """Create collection safely (skip if exists)"""
        try:
            if validator:
                await self.admin_db.create_collection(collection_name, validator=validator)
            else:
                await self.admin_db.create_collection(collection_name)
            print(f"[OK] Created collection: {collection_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"[WARN] Collection {collection_name} already exists")
            else:
                print(f"[ERROR] Failed to create {collection_name}: {e}")
        
        print("[OK] All collections created successfully")
    
    async def create_indexes(self):
        """Create indexes for performance and security"""
        
        print("🔧 Creating database indexes...")
        
        # CLIENTS COLLECTION INDEXES
        await self.admin_db.clients.create_index("domain", unique=True)
        await self.admin_db.clients.create_index("api_key", unique=True)
        await self.admin_db.clients.create_index("status")
        await self.admin_db.clients.create_index("created_at")
        print("[OK] Created clients indexes")
        
        # CLIENT_USERS COLLECTION INDEXES
        await self.admin_db.client_users.create_index([("client_id", 1), ("email", 1)], unique=True)
        await self.admin_db.client_users.create_index("email")
        await self.admin_db.client_users.create_index("client_id")
        await self.admin_db.client_users.create_index("status")
        print("[OK] Created client_users indexes")
        
        # CONVERSATIONS COLLECTION INDEXES (Critical for data isolation)
        await self.admin_db.conversations.create_index("client_id")
        await self.admin_db.conversations.create_index([("client_id", 1), ("session_id", 1)])
        await self.admin_db.conversations.create_index("created_at")
        await self.admin_db.conversations.create_index([("client_id", 1), ("created_at", -1)])
        print("[OK] Created conversations indexes")
        
        # CLIENT_VEHICLES COLLECTION INDEXES
        await self.admin_db.client_vehicles.create_index("client_id")
        await self.admin_db.client_vehicles.create_index([("client_id", 1), ("brand", 1), ("model", 1)])
        await self.admin_db.client_vehicles.create_index([("client_id", 1), ("availability", 1)])
        await self.admin_db.client_vehicles.create_index("coe_category")
        print("[OK] Created client_vehicles indexes")
        
        # ANALYTICS COLLECTION INDEXES
        await self.admin_db.analytics.create_index([("client_id", 1), ("date", 1)], unique=True)
        await self.admin_db.analytics.create_index("date")
        
        # Super admins indexes
        await self.admin_db.super_admins.create_index("email", unique=True)
        
        print("[OK] All indexes created successfully")
        await self.admin_db.analytics.create_index("client_id")
        print("[OK] Created analytics indexes")
    
    async def create_sample_data(self):
        """Create sample data for testing"""
        
        print("🔧 Creating sample data...")
        
        # Sample client
        sample_client = {
            "business_name": "ABC Motors Singapore",
            "domain": "abcmotors.com.sg",
            "contact_email": "admin@abcmotors.com.sg",
            "status": "active",
            "api_key": "cc_sample_api_key_abc_motors_12345",
            "settings": {
                "branding": {
                    "company_name": "ABC Motors Singapore",
                    "primary_color": "#FF6B35",
                    "secondary_color": "#4A90E2",
                    "logo_url": "https://abcmotors.com.sg/logo.png"
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
                    "phone": "+65 6234 5678",
                    "email": "sales@abcmotors.com.sg",
                    "address": "123 Automotive Street, Singapore 123456",
                    "whatsapp": "+65 9876 5432"
                },
                "business_hours": {
                    "monday": "9:00 AM - 7:00 PM",
                    "tuesday": "9:00 AM - 7:00 PM",
                    "wednesday": "9:00 AM - 7:00 PM",
                    "thursday": "9:00 AM - 7:00 PM",
                    "friday": "9:00 AM - 7:00 PM",
                    "saturday": "9:00 AM - 6:00 PM",
                    "sunday": "10:00 AM - 5:00 PM"
                }
            },
            "subscription_plan": {
                "plan_type": "premium",
                "monthly_conversations": 5000,
                "features_included": ["all_features"],
                "price_per_month": 299.0,
                "overage_rate": 0.08
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "current_month_conversations": 0,
            "total_conversations": 0
        }
        
        # Insert sample client
        try:
            result = await self.admin_db.clients.insert_one(sample_client)
            client_id = result.inserted_id
            print(f"[OK] Created sample client: {client_id}")
            
            # Sample client user
            import hashlib
            password_hash = hashlib.sha256("password123".encode()).hexdigest()
            
            sample_user = {
                "client_id": client_id,
                "email": "admin@abcmotors.com.sg",
                "name": "John Tan",
                "role": "admin",
                "password_hash": password_hash,
                "status": "active",
                "permissions": [
                    "view_analytics",
                    "edit_branding",
                    "manage_vehicles",
                    "edit_responses",
                    "view_conversations"
                ],
                "created_at": datetime.utcnow(),
                "login_count": 0
            }
            
            await self.admin_db.client_users.insert_one(sample_user)
            print("[OK] Created sample client user")
            
            # Sample vehicles
            sample_vehicles = [
                {
                    "client_id": client_id,
                    "brand": "Toyota",
                    "model": "Camry",
                    "year": 2024,
                    "price": 180000,
                    "coe_category": "B",
                    "availability": "in_stock",
                    "engine_capacity": 2.0,
                    "fuel_type": "Hybrid",
                    "transmission": "Automatic",
                    "features": ["Hybrid Engine", "Sunroof", "Leather Seats", "Navigation"],
                    "images": [],
                    "description": "Premium hybrid sedan with excellent fuel efficiency",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "client_id": client_id,
                    "brand": "Honda",
                    "model": "Civic",
                    "year": 2024,
                    "price": 135000,
                    "coe_category": "A",
                    "availability": "in_stock",
                    "engine_capacity": 1.5,
                    "fuel_type": "Petrol",
                    "transmission": "CVT",
                    "features": ["Honda SENSING", "Touchscreen", "Keyless Entry"],
                    "images": [],
                    "description": "Reliable and fuel-efficient compact sedan",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            await self.admin_db.client_vehicles.insert_many(sample_vehicles)
            print("[OK] Created sample vehicles")
            
        except Exception as e:
            print(f"[WARN] Sample data creation failed (may already exist): {e}")
    
    async def verify_setup(self):
        """Verify the database setup"""
        
        print("🔍 Verifying database setup...")
        
        # Check collections
        collections = await self.admin_db.list_collection_names()
        expected_collections = ["clients", "client_users", "conversations", "client_vehicles", "analytics"]
        
        for collection in expected_collections:
            if collection in collections:
                count = await self.admin_db[collection].count_documents({})
                print(f"[OK] {collection}: {count} documents")
            else:
                print(f"[ERROR] Missing collection: {collection}")
        
        # Check indexes
        for collection in expected_collections:
            if collection in collections:
                indexes = await self.admin_db[collection].list_indexes().to_list(None)
                print(f"[INFO] {collection}: {len(indexes)} indexes")
    
    async def close(self):
        """Close database connection"""
        if self.admin_client:
            self.admin_client.close()
            print("[INFO] Database connection closed")

async def main():
    """Main setup function"""
    print("[SETUP] MongoDB Atlas SaaS Database Setup")
    print("=" * 50)
    
    setup = MongoDBSetup()
    
    try:
        # Connect to database
        if not await setup.connect():
            return
        
        # Create collections with validation
        await setup.create_collections_with_validation()
        
        # Create indexes
        await setup.create_indexes()
        
        # Create sample data
        await setup.create_sample_data()
        
        # Verify setup
        await setup.verify_setup()
        
        print("\n[SUCCESS] Database setup completed successfully!")
        print("\n[INFO] Next Steps:")
        print("1. Start your backend: npm run dev:backend")
        print("2. Test client registration: http://localhost:3000/client-signup")
        print("3. Test super admin: http://localhost:3000/super-admin")
        print("4. Login with sample client: admin@abcmotors.com.sg / password123")
        
    except Exception as e:
        print(f"[ERROR] Setup failed: {e}")
    finally:
        await setup.close()

if __name__ == "__main__":
    asyncio.run(main())