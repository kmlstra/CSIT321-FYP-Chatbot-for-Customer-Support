from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB connection strings
ADMIN_CONNECTION = "mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"
DATABASE_NAME = "automotive_chatbot_saas"

# Global database connection
admin_client = None
admin_db = None

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    global admin_client, admin_db
    # Startup: Initialize MongoDB connection
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

# Authentication helper functions
import hashlib
import jwt
from datetime import timedelta

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
        "endpoints": {
            "client_login": "/api/auth/client-login",
            "super_admin_login": "/api/auth/super-admin-login",
            "client_registration": "/api/client-registration/register",
            "health": "/health",
            "docs": "/docs"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    db_status = "connected" if admin_db else "disconnected"
    
    return {
        "status": "healthy",
        "version": "3.0.0",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# CLIENT AUTHENTICATION
@app.post("/api/auth/client-login")
async def client_login(request: ClientLoginRequest):
    """Client user login endpoint"""
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

# CLIENT REGISTRATION
@app.post("/api/client-registration/register")
async def register_new_client(request: ClientRegistrationRequest):
    """Register a new automotive business client"""
    try:
        # Check if domain already exists
        existing_client = await admin_db.clients.find_one({"domain": request.domain})
        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain already registered"
            )
        
        # Check if email already exists
        existing_email = await admin_db.clients.find_one({"contact_email": request.contact_email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate API key
        import secrets
        api_key = f"cc_{secrets.token_urlsafe(32)}"
        
        # Create client document
        client_data = {
            "business_name": request.business_name,
            "domain": request.domain,
            "contact_email": request.contact_email,
            "status": "pending",
            "api_key": api_key,
            "settings": {
                "branding": {
                    "company_name": request.business_name,
                    "primary_color": "#4F46E5",
                    "secondary_color": "#7C3AED",
                    "logo_url": None
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
                "contact_info": request.contact_info,
                "business_hours": {
                    "monday": "9:00 AM - 6:00 PM",
                    "tuesday": "9:00 AM - 6:00 PM",
                    "wednesday": "9:00 AM - 6:00 PM",
                    "thursday": "9:00 AM - 6:00 PM",
                    "friday": "9:00 AM - 6:00 PM",
                    "saturday": "9:00 AM - 5:00 PM",
                    "sunday": "Closed"
                }
            },
            "subscription_plan": {
                "plan_type": "premium",
                "monthly_conversations": 5000,
                "price_per_month": 299.0
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "current_month_conversations": 0,
            "total_conversations": 0
        }
        
        # Insert client
        result = await admin_db.clients.insert_one(client_data)
        client_id = str(result.inserted_id)
        
        # Create admin user for the client
        admin_user_data = request.admin_user
        user_data = {
            "client_id": result.inserted_id,
            "email": admin_user_data["email"],
            "name": admin_user_data["name"],
            "role": "admin",
            "password_hash": hash_password(admin_user_data["password"]),
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
        
        await admin_db.client_users.insert_one(user_data)
        
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
        clients = []
        async for client in admin_db.clients.find({}):
            client["id"] = str(client["_id"])
            del client["_id"]
            clients.append(client)
        
        return {"clients": clients, "total": len(clients)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch clients: {str(e)}"
        )

@app.post("/api/super-admin/clients/{client_id}/approve")
async def approve_client(client_id: str):
    """Approve a pending client account"""
    try:
        from bson import ObjectId
        
        result = await admin_db.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "status": "active",
                    "activated_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return {
            "success": True,
            "message": f"Client {client_id} approved successfully",
            "client_id": client_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve client: {str(e)}"
        )

@app.get("/api/super-admin/metrics")
async def get_system_metrics():
    """Get system-wide metrics"""
    try:
        # Count clients by status
        total_clients = await admin_db.clients.count_documents({})
        active_clients = await admin_db.clients.count_documents({"status": "active"})
        pending_clients = await admin_db.clients.count_documents({"status": "pending"})
        
        # Count conversations today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        conversations_today = await admin_db.conversations.count_documents({
            "created_at": {"$gte": today}
        })
        
        return {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "pending_approvals": pending_clients,
            "total_conversations_today": conversations_today,
            "revenue_this_month": active_clients * 299.0,  # Mock calculation
            "system_uptime": 99.9
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn