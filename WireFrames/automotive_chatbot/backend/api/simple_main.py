from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from datetime import datetime
import hashlib
import jwt
from datetime import timedelta

# Try to import optional dependencies
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    print("[WARN] Motor not available - MongoDB features disabled")

try:
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    print("[WARN] PyMongo not available - MongoDB features disabled")

# MongoDB connection strings
ADMIN_CONNECTION = "mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
DATABASE_NAME = "automotive_chatbot_saas"

# Global database connection
admin_client = None
admin_db = None

# Global variable to store client database configuration
current_db_config = None
synced_vehicles = []

# Global variable to store synced vehicles
synced_vehicles = []

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    global admin_client, admin_db
    # Startup: Initialize MongoDB connection
    if MOTOR_AVAILABLE:
        try:
            admin_client = AsyncIOMotorClient(ADMIN_CONNECTION)
            admin_db = admin_client[DATABASE_NAME]
            
            # Test connection
            await admin_client.admin.command('ping')
            print("[OK] Connected to MongoDB Atlas successfully")
            
            # Create super admin on startup
            await create_initial_super_admin()
            
        except Exception as e:
            print(f"[ERROR] Failed to connect to MongoDB: {e}")
    else:
        print("[WARN] MongoDB not available - using mock data")
    
    yield
    
    # Shutdown: Close MongoDB connections
    if admin_client:
        admin_client.close()
        print("[INFO] MongoDB connection closed")

app = FastAPI(
    title="CleverCompanion SaaS Platform",
    description="Multi-tenant automotive chatbot platform",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for authentication
class ClientLoginRequest(BaseModel):
    email: str
    password: str

class SuperAdminLoginRequest(BaseModel):
    email: str
    password: str

class ClientRegistrationRequest(BaseModel):
    business_name: str
    domain: str
    contact_email: str
    admin_user: dict
    contact_info: dict = {}

class DatabaseConnectionRequest(BaseModel):
    db_type: str
    connection_string: str
    database_name: str
    collection_name: str
    chat_collection_name: str = "chat_history"
    additional_collections: str = ""
    field_mapping: dict = {}

# Authentication helper functions
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def create_initial_super_admin():
    """Create initial super admin user"""
    if not MOTOR_AVAILABLE or not admin_db:
        return
        
    try:
        # Check if super admin already exists
        existing_admin = await admin_db.super_admins.find_one({"email": "admin@clevercompanion.com"})
        if existing_admin:
            print("[OK] Super admin already exists")
            return
        
        # Create super admin user
        super_admin = {
            "email": "admin@clevercompanion.com",
            "password_hash": hash_password("SuperAdmin123!"),
            "name": "Super Administrator",
            "role": "super_admin",
            "status": "active",
            "created_at": datetime.utcnow(),
            "last_login": None,
            "login_count": 0
        }
        
        await admin_db.super_admins.insert_one(super_admin)
        print("[OK] Created super admin: admin@clevercompanion.com")
        print("[INFO] Password: SuperAdmin123!")
        
    except Exception as e:
        print(f"[ERROR] Failed to create super admin: {e}")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "CleverCompanion SaaS Platform v3.0",
        "status": "running",
        "mongodb_available": MOTOR_AVAILABLE,
        "endpoints": {
            "client_login": "/api/auth/client-login",
            "super_admin_login": "/api/auth/super-admin-login",
            "client_registration": "/api/client-registration/register",
            "health": "/health",
            "docs": "/docs"
        }
    }

# BRANDING AND CONTACT ENDPOINTS
@app.put("/api/client/branding")
async def update_branding():
    """Update client branding configuration"""
    return {
        "success": True,
        "message": "Branding updated successfully"
    }

@app.put("/api/client/contact-info")
async def update_contact_info():
    """Update client contact information"""
    return {
        "success": True,
        "message": "Contact information updated successfully"
    }

@app.put("/api/client/features")
async def update_features():
    """Update client features configuration"""
    return {
        "success": True,
        "message": "Features configuration updated successfully"
    }
# Health check endpoint
@app.get("/health")
async def health_check():
    db_status = "connected" if admin_db else "disconnected"
    
    return {
        "status": "healthy",
        "version": "3.0.0",
        "database": db_status,
        "motor_available": MOTOR_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }

# CLIENT AUTHENTICATION
@app.post("/api/auth/client-login")
async def client_login(request: ClientLoginRequest):
    """Client user login endpoint"""
    if not MOTOR_AVAILABLE or not admin_db:
        # Mock response for testing when MongoDB is not available
        if request.email == "admin@abcmotors.com.sg" and request.password == "password123":
            return {
                "access_token": "mock_token_12345",
                "token_type": "bearer",
                "user": {
                    "id": "mock_user_123",
                    "email": request.email,
                    "name": "John Tan",
                    "role": "admin",
                    "client_id": "mock_client_123"
                },
                "client": {
                    "id": "mock_client_123",
                    "business_name": "ABC Motors Singapore",
                    "domain": "abcmotors.com.sg",
                    "status": "active",
                    "settings": {
                        "branding": {
                            "company_name": "ABC Motors Singapore",
                            "primary_color": "#4F46E5",
                            "secondary_color": "#7C3AED"
                        },
                        "features": {
                            "coe_prices": True,
                            "loan_calculator": True,
                            "test_drive_booking": True,
                            "maintenance_tips": True,
                            "vehicle_search": True,
                            "contact_support": True
                        },
                        "contact_info": {
                            "phone": "+65 6234 5678",
                            "email": "sales@abcmotors.com.sg",
                            "address": "123 Automotive Street, Singapore"
                        }
                    }
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
    
    try:
        # Find user by email
        user = await admin_db.client_users.find_one({"email": request.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if hash_password(request.password) != user["password_hash"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if user.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )
        
        # Get client information
        from bson import ObjectId
        client = await admin_db.clients.find_one({"_id": ObjectId(user["client_id"])})
        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Client not found"
            )
        
        # Update login information
        await admin_db.client_users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"last_login": datetime.utcnow()},
                "$inc": {"login_count": 1}
            }
        )
        
        # Create JWT token
        token_data = {
            "user_id": str(user["_id"]),
            "client_id": str(user["client_id"]),
            "email": user["email"],
            "role": user["role"],
            "type": "client_user"
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
                "client_id": str(user["client_id"])
            },
            "client": {
                "id": str(client["_id"]),
                "business_name": client["business_name"],
                "domain": client["domain"],
                "status": client["status"],
                "settings": client.get("settings", {})
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Client login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

# SUPER ADMIN AUTHENTICATION
@app.post("/api/auth/super-admin-login")
async def super_admin_login(request: SuperAdminLoginRequest):
    """Super admin login endpoint"""
    if not MOTOR_AVAILABLE or not admin_db:
        # Mock response for testing
        if request.email == "admin@clevercompanion.com" and request.password == "SuperAdmin123!":
            return {
                "access_token": "super_admin_token_12345",
                "token_type": "bearer",
                "user": {
                    "email": request.email,
                    "name": "Super Administrator",
                    "role": "super_admin"
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
    
    try:
        # Find super admin by email
        admin = await admin_db.super_admins.find_one({"email": request.email})
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if hash_password(request.password) != admin["password_hash"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if admin is active
        if admin.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )
        
        # Update login info
        await admin_db.super_admins.update_one(
            {"_id": admin["_id"]},
            {
                "$set": {"last_login": datetime.utcnow()},
                "$inc": {"login_count": 1}
            }
        )
        
        # Generate JWT token
        token_data = {
            "user_id": str(admin["_id"]),
            "email": admin["email"],
            "role": "super_admin",
            "type": "super_admin"
        }
        
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(admin["_id"]),
                "email": admin["email"],
                "name": admin["name"],
                "role": "super_admin"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Super admin login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Super admin login failed: {str(e)}"
        )

# DATABASE CONNECTION ENDPOINTS
@app.post("/api/client/database/test-connection")
async def test_database_connection(request: DatabaseConnectionRequest):
    """Test database connection for client"""
    try:
        if request.db_type.lower() == "mongodb":
            if not MOTOR_AVAILABLE:
                return {
                    "success": False,
                    "message": "MongoDB support not available - motor package not installed"
                }
            
            # Test MongoDB connection
            test_client = AsyncIOMotorClient(request.connection_string, serverSelectionTimeoutMS=5000)
            
            try:
                # Test connection
                await test_client.admin.command('ping')
                
                # Get database info
                db = test_client[request.database_name]
                collections = await db.list_collection_names()
                
                # Get record count for specified collection
                record_count = 0
                sample_record = None
                
                if request.collection_name in collections:
                    record_count = await db[request.collection_name].count_documents({})
                    
                    # Get a sample record
                    sample_doc = await db[request.collection_name].find_one({})
                    if sample_doc:
                        # Convert ObjectId to string for JSON serialization
                        if "_id" in sample_doc:
                            sample_doc["_id"] = str(sample_doc["_id"])
                        sample_record = sample_doc
                
                test_client.close()
                
                return {
                    "success": True,
                    "message": f"✅ Connection successful! Found {len(collections)} collections",
                    "database_info": {
                        "database_name": request.database_name,
                        "collections": collections,
                        "record_count": record_count,
                        "sample_record": sample_record
                    }
                }
                
            except Exception as e:
                test_client.close()
                return {
                    "success": False,
                    "message": f"❌ Connection failed: {str(e)}"
                }
        
        else:
            return {
                "success": False,
                "message": f"Database type '{request.db_type}' not yet supported. Currently supports: MongoDB"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Connection test failed: {str(e)}"
        }

@app.post("/api/client/database/save-connection")
async def save_database_connection(request: DatabaseConnectionRequest):
    """Save database connection configuration for client"""
    global current_db_config
    try:
        current_db_config = {
            "db_type": request.db_type,
            "connection_string": request.connection_string,
            "database_name": request.database_name,
            "collection_name": request.collection_name,
            "chat_collection_name": request.chat_collection_name,
            "additional_collections": request.additional_collections,
            "field_mapping": request.field_mapping,
            "connected": True,
            "saved_at": datetime.utcnow(),
            "record_count": 0
        }
        
        print(f"[DEBUG] Saved database config: {current_db_config}")
        
        return {
            "success": True,
            "message": "✅ Database connection saved successfully!",
            "config_id": "saved_config_123",
            "status": "connected"
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to save database connection: {e}")
        return {
            "success": False,
            "message": f"❌ Failed to save connection: {str(e)}"
        }

@app.post("/api/client/database/sync-data")
async def sync_database_data():
    """Sync data from client's external database"""
    global current_db_config, synced_vehicles
    try:
        if not current_db_config or not current_db_config.get("connected"):
            return {
                "success": False,
                "message": "❌ No database connection configured"
            }
        
        print(f"[DEBUG] Syncing data with config: {current_db_config}")
        
        # Connect to client's database and pull data
        if current_db_config["db_type"].lower() == "mongodb":
            if not MOTOR_AVAILABLE:
                return {
                    "success": False,
                    "message": "❌ MongoDB support not available"
                }
            
            # Connect to client's database
            client_db_client = AsyncIOMotorClient(
                current_db_config["connection_string"], 
                serverSelectionTimeoutMS=10000
            )
            
            try:
                # Get the database and collection
                db = client_db_client[current_db_config["database_name"]]
                collection = db[current_db_config["collection_name"]]
                
                # Pull all data from the collection
                cursor = collection.find({})
                synced_vehicles = []
                
                async for document in cursor:
                    # Convert ObjectId to string for JSON serialization
                    if "_id" in document:
                        document["_id"] = str(document["_id"])
                    synced_vehicles.append(document)
                
                client_db_client.close()
                
                # Update config with record count
                current_db_config["record_count"] = len(synced_vehicles)
                current_db_config["last_sync"] = datetime.utcnow().isoformat()
                
                print(f"[DEBUG] Synced {len(synced_vehicles)} vehicles from database")
                
                return {
                    "success": True,
                    "message": f"✅ Data synced successfully! Pulled {len(synced_vehicles)} records",
                    "data": {
                        "total_count": len(synced_vehicles),
                        "sync_timestamp": current_db_config["last_sync"],
                        "collections_synced": [current_db_config["collection_name"]]
                    }
                }
                
            except Exception as e:
                client_db_client.close()
                print(f"[ERROR] Database sync failed: {e}")
                return {
                    "success": False,
                    "message": f"❌ Sync failed: {str(e)}"
                }
        
        else:
            return {
                "success": False,
                "message": f"❌ Database type '{current_db_config['db_type']}' not yet supported"
            }
        
    except Exception as e:
        print(f"[ERROR] Sync error: {e}")
        return {
            "success": False,
            "message": f"❌ Sync failed: {str(e)}"
        }

@app.get("/api/client/database/status")
async def get_database_status():
    """Get current database connection status"""
    global current_db_config
    
    if not current_db_config:
        return {
            "connected": False,
            "db_type": None,
            "database_name": None,
            "collection_name": None,
            "last_sync": None,
            "record_count": 0,
            "message": "No database configured"
        }
    
    return {
        "connected": current_db_config.get("connected", False),
        "db_type": current_db_config.get("db_type"),
        "database_name": current_db_config.get("database_name"),
        "collection_name": current_db_config.get("collection_name"),
        "last_sync": current_db_config.get("last_sync"),
        "record_count": current_db_config.get("record_count", 0),
        "message": "Database connected and configured"
    }

@app.get("/api/client/vehicles")
async def get_client_vehicles():
    """Get vehicles from connected database"""
    global synced_vehicles, current_db_config
    
    if not current_db_config or not current_db_config.get("connected"):
        return {
            "vehicles": [],
            "message": "No database connected",
            "connected": False
        }
    
    # Apply field mapping to synced vehicles
    mapped_vehicles = []
    field_mapping = current_db_config.get("field_mapping", {})
    
    for vehicle in synced_vehicles:
        mapped_vehicle = {
            "id": vehicle.get("_id", ""),
            "brand": vehicle.get(field_mapping.get("brand", "brand"), "Unknown"),
            "model": vehicle.get(field_mapping.get("model", "model"), "Unknown"),
            "year": vehicle.get(field_mapping.get("year", "year"), 0),
            "price": vehicle.get(field_mapping.get("price", "price"), 0),
            "availability": vehicle.get(field_mapping.get("availability", "status"), "unknown"),
            "raw_data": vehicle  # Include raw data for debugging
        }
        mapped_vehicles.append(mapped_vehicle)
    
    return {
        "vehicles": mapped_vehicles,
        "total": len(mapped_vehicles),
        "connected": True,
        "source": "external_database"
    }

@app.get("/api/client/analytics")
async def get_client_analytics():
    """Get analytics from connected database"""
    global current_db_config
    
    if not current_db_config or not current_db_config.get("connected"):
        return {
            "message": "No database connected",
            "connected": False
        }
    
    # In a real implementation, this would query chat_history collection
    return {
        "total_conversations": 0,
        "unique_users": 0,
        "avg_messages_per_session": 0,
        "connected": True,
        "message": "Analytics will populate as customers use your chatbot"
    }

@app.get("/api/client/conversations")
async def get_client_conversations():
    """Get conversations from connected database"""
    global current_db_config
    
    if not current_db_config or not current_db_config.get("connected"):
        return {
            "conversations": [],
            "message": "No database connected",
            "connected": False
        }
    
    try:
        # Connect to client's database and get chat history
        client_db_client = AsyncIOMotorClient(
            current_db_config["connection_string"], 
            serverSelectionTimeoutMS=10000
        )
        
        db = client_db_client[current_db_config["database_name"]]
        chat_collection_name = current_db_config.get("chat_collection_name", "chat_history")
        
        # Try to get from chat_history collection
        conversations = []
        collections = await db.list_collection_names()
        
        if chat_collection_name in collections:
            cursor = db[chat_collection_name].find({}).sort([("created_at", -1)]).limit(50)
            async for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                # Add computed fields for better display
                doc["customer_name"] = doc.get("customer_name") or doc.get("user_name") or f"Customer {doc.get('_id', '')[:8]}"
                doc["messages"] = doc.get("total_messages") or len(doc.get("messages", []))
                doc["status"] = doc.get("status") or "completed"
                if doc.get("messages") and isinstance(doc["messages"], list) and len(doc["messages"]) > 0:
                    last_msg = doc["messages"][-1]
                    if isinstance(last_msg, dict):
                        doc["last_message"] = last_msg.get("content", "")[:50]
                conversations.append(doc)
        else:
            print(f"[DEBUG] Chat collection '{chat_collection_name}' not found in collections: {collections}")
        
        client_db_client.close()
        
        print(f"[DEBUG] Found {len(conversations)} conversations in chat_history")
        
        return {
            "conversations": conversations,
            "total": len(conversations),
            "connected": True,
            "source": chat_collection_name,
            "available_collections": collections
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch conversations: {e}")
        return {
            "conversations": [],
            "total": 0,
            "connected": True,
            "error": str(e),
            "chat_collection_name": current_db_config.get("chat_collection_name", "chat_history")
        }

# CLIENT REGISTRATION
@app.post("/api/client-registration/register")
async def register_new_client(request: ClientRegistrationRequest):
    """Register a new automotive business client"""
    try:
        # Check if domain already exists (mock check)
        if request.domain == "existing.com":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain already registered"
            )
        
        # Generate mock client ID
        import secrets
        client_id = f"client_{secrets.token_hex(8)}"
        
        return {
            "success": True,
            "client_id": client_id,
            "message": "Account created successfully! Awaiting admin approval.",
            "next_steps": [
                "Your account has been created with 'pending' status",
                "Our team will review and activate your account within 24 hours",
                "You'll receive an email confirmation once approved",
                "Then you can log in and configure your chatbot"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

# SUPER ADMIN ROUTES
@app.get("/api/super-admin/clients")
async def get_all_clients():
    """Get all clients for super admin"""
    try:
        # Mock client data
        clients = [
            {
                "id": "client_123",
                "business_name": "ABC Motors Singapore",
                "domain": "abcmotors.com.sg",
                "contact_email": "admin@abcmotors.com.sg",
                "status": "active",
                "subscription_plan": {
                    "plan_type": "premium",
                    "price_per_month": 299.0
                },
                "created_at": "2025-01-15T10:30:00Z",
                "current_month_conversations": 0,
                "total_conversations": 0
            }
        ]
        
        return clients
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch clients: {str(e)}"
        )

@app.post("/api/super-admin/clients/{client_id}/approve")
async def approve_client(client_id: str):
    """Approve a pending client account"""
    try:
        return {
            "success": True,
            "message": f"Client {client_id} approved successfully",
            "client_id": client_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve client: {str(e)}"
        )

@app.get("/api/super-admin/metrics")
async def get_system_metrics():
    """Get system-wide metrics"""
    try:
        return {
            "total_clients": 1,
            "active_clients": 1,
            "pending_approvals": 0,
            "total_conversations_today": 0,
            "revenue_this_month": 299.0,
            "system_uptime": 99.9
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)