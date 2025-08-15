from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import os
import json
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "../.env")
if Path(env_path).exists():
    load_dotenv(dotenv_path=env_path)
else:
    print("⚠️ Warning: backend/.env file not found. API may not function properly.")

# Import existing modules
from .config import Settings
from .middleware.conversation_middleware import ConversationAPI
from .middleware.auto_logger import ConversationLogger
from .auth.client_auth import get_current_client_user

settings = Settings()

# Import database manager to use environment variables
from .config.database import get_real_admin_db, close_database_connection

# Database configuration from environment variables
DATABASE_NAME = "automotive_chatbot_saas"

# Global database connection
admin_db = None

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

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    global admin_db
    # Startup: Initialize MongoDB connection using environment variables
    try:
        # Use the database manager which loads from .env
        admin_db = await get_real_admin_db()
        
        if admin_db:
            print("[OK] Connected to MongoDB Atlas successfully using environment variables")
        else:
            raise Exception("Failed to get database connection from environment variables")
        
        # Create super admin on startup
        await create_initial_super_admin()
        
        # Set database for widget API after connection is established
        try:
            from .widget_api.multi_tenant_chat import set_database
            set_database(admin_db)
            print("[OK] Widget API database connection set")
        except ImportError:
            print("[WARNING] Widget API not available for database setup")
        
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
    
    print("Starting CleverCompanion SaaS Platform v3.0...")
    yield
    
    # Shutdown: Close MongoDB connections
    await close_database_connection()
    print("Shutting down CleverCompanion SaaS Platform v3.0...")

app = FastAPI(
    title="CleverCompanion SaaS Platform",
    description="Multi-tenant automotive chatbot platform with advanced AI capabilities",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware configuration with optimized settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Mount static files directory
static_path = os.path.join(os.path.dirname(__file__), "../static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "CleverCompanion SaaS Platform v3.0",
        "status": "running",
        "features": [
            "Multi-tenant architecture",
            "Real-time COE pricing from LTA",
            "RAG-enhanced AI responses",
            "Embeddable widget API",
            "VectorDB knowledge base",
            "LangChain integration",
            "Client management system",
            "Super admin dashboard"
        ],
        "endpoints": {
            "client_login": "/api/auth/client-login",
            "super_admin_login": "/api/auth/super-admin-login",
            "client_registration": "/api/client-registration/register",
            "health": "/health",
            "docs": "/docs",
            "widget_demo": "/clevercompanion-widget.js"
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
        "services": {
            "api": "running",
            "information_service": "available",
            "coe_service": "available",
            "rag_service": "available" if os.getenv("OPENAI_API_KEY") else "limited"
        }
    }

# Environment configuration endpoint
@app.get("/api/config/env")
async def get_environment_config():
    """Serve environment configuration for frontend"""
    return {
        "DOMAIN": os.getenv("DOMAIN", "http://localhost"),
        "BACKEND_URL": os.getenv("BACKEND_URL", f"{os.getenv('DOMAIN', 'http://localhost')}:8000"),
        "FRONTEND_URL": os.getenv("FRONTEND_URL", f"{os.getenv('DOMAIN', 'http://localhost')}:3000"),
        "RASA_URL": os.getenv("RASA_URL", f"{os.getenv('DOMAIN', 'http://localhost')}:5005"),
        "RASA_ACTIONS_URL": os.getenv("RASA_ACTIONS_URL", f"{os.getenv('DOMAIN', 'http://localhost')}:5055"),
        "PROFILE_PICTURE_URL": os.getenv("PROFILE_PICTURE_URL", f"{os.getenv('DOMAIN', 'http://localhost')}:8000/static/boy.png")
    }

# Widget JavaScript file endpoint
@app.get("/clevercompanion-widget.js")
async def serve_widget_js():
    """Serve the clevercompanion widget JavaScript file"""
    from fastapi.responses import FileResponse
    import os
    
    # Get the absolute path to the static directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_dir, "..", "static")
    widget_path = os.path.join(static_dir, "clevercompanion-widget.js")
    widget_path = os.path.abspath(widget_path)
    
    # Widget file lookup
    
    if not os.path.exists(widget_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Widget JavaScript file not found at {widget_path}"
        )
    
    return FileResponse(
        path=widget_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*"
        }
    )

# Page interactions JavaScript file endpoint
@app.get("/page-interactions.js")
async def serve_page_interactions_js():
    """Serve the page-interactions JavaScript file"""
    from fastapi.responses import FileResponse
    import os
    
    # Get the absolute path to the static directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_dir, "..", "static")
    interactions_path = os.path.join(static_dir, "page-interactions.js")
    interactions_path = os.path.abspath(interactions_path)
    
    # Page interactions file lookup
    
    if not os.path.exists(interactions_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page interactions JavaScript file not found at {interactions_path}"
        )
    
    return FileResponse(
        path=interactions_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*"
        }
    )

# CLIENT AUTHENTICATION
@app.post("/api/auth/client-login")
async def client_login(request: ClientLoginRequest):
    """Client user login endpoint"""
    global admin_db
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
        
        # Check client status - this is the key fix for the login issue
        if client.get("status") == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is pending approval. Please wait for admin approval before logging in."
            )
        elif client.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your client account is not active. Please contact support."
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
    global admin_db
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
                    "appointment_booking": True,
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
    global admin_db
    try:
        clients = []
        async for client in admin_db.clients.find({}):
            client["id"] = str(client["_id"])
            del client["_id"]
            clients.append(client)
        
        result = {"clients": clients, "total": len(clients)}
        return result
        
    except Exception as e:
        print(f"[ERROR] get_all_clients failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch clients: {str(e)}"
        )

@app.post("/api/super-admin/clients/{client_id}/approve")
async def approve_client(client_id: str):
    """Approve a pending client account"""
    global admin_db
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
    global admin_db
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

# EXISTING FUNCTIONALITY - PRESERVED FOR BACKWARD COMPATIBILITY
from fastapi import APIRouter

# Essential boundaries for RASA actions
vehicle_router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])
coe_router = APIRouter(prefix="/api/coe", tags=["coe"])

@vehicle_router.get("/")
async def get_vehicles_fallback():
    return {"success": True, "vehicles": [], "message": "Vehicle service initializing"}

@coe_router.get("/prices")
async def get_coe_prices_fallback():
    return {"success": True, "data": {"category_a": {"current": 95000}}, "message": "COE service initializing"}

app.include_router(vehicle_router)
app.include_router(coe_router)

# Conversation Management API
conversation_router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@conversation_router.get("/history/{session_id}")
async def get_conversation_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to retrieve")
):
    """Get conversation history for a specific session."""
    try:
        result = ConversationAPI.get_conversation_history(session_id, limit)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation history: {str(e)}")

@conversation_router.get("/sessions/active")
async def get_active_sessions():
    """Get information about currently active sessions."""
    try:
        result = ConversationAPI.get_active_sessions()
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving active sessions: {str(e)}")

@conversation_router.post("/cleanup")
async def cleanup_expired_sessions(background_tasks: BackgroundTasks):
    """Clean up expired conversation sessions."""
    try:
        # Run cleanup in background to avoid blocking
        def cleanup_task():
            return ConversationAPI.cleanup_expired_sessions()
        
        background_tasks.add_task(cleanup_task)
        return JSONResponse(content={
            "message": "Cleanup task started",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting cleanup task: {str(e)}")

@conversation_router.get("/stats")
async def get_conversation_stats():
    """Get conversation statistics."""
    try:
        active_sessions = ConversationAPI.get_active_sessions()
        return JSONResponse(content={
            "active_sessions": active_sessions.get("active_sessions", 0),
            "session_timeout_minutes": 30,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation stats: {str(e)}")

app.include_router(conversation_router)

# Chat History Viewer API (for frontend compatibility)
chat_history_router = APIRouter(prefix="/api/conversation", tags=["chat-history"])

@chat_history_router.get("/history")
async def get_all_conversations(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of conversations to retrieve")
):
    """Get all conversation history for chat history viewer."""
    try:
        # Get all active sessions and their conversation data
        active_sessions = ConversationAPI.get_active_sessions()
        all_conversations = []
        
        # For now, return a sample structure that matches frontend expectations
        sample_conversations = [
            {
                "id": "conv_001",
                "timestamp": "2024-01-15T10:30:00Z",
                "content": "User: Hello\nBot: Hi there! How can I help you today?\nUser: I need information about car loans\nBot: I'd be happy to help you with car loan information.",
                "message_count": 4
            },
            {
                "id": "conv_002", 
                "timestamp": "2024-01-15T11:45:00Z",
                "content": "User: What are the COE prices?\nBot: Let me get the latest COE prices for you.",
                "message_count": 2
            },
            {
                "id": "conv_003",
                "timestamp": "2024-01-15T14:20:00Z", 
                "content": "User: I want to contact support\nBot: Here's how you can reach our support team.",
                "message_count": 2
            }
        ]
        
        return JSONResponse(content={
            "success": True,
            "conversations": sample_conversations[:limit]
        })
    except Exception as e:
        logger.error(f"Error in get_all_conversations: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error retrieving conversations: {str(e)}"
        }, status_code=500)

@chat_history_router.get("/history/{conversation_id}")
async def get_conversation_for_viewer(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to retrieve")
):
    """Get conversation history for chat history viewer (frontend compatibility endpoint)."""
    try:
        # Use the existing ConversationAPI with session_id as conversation_id
        result = ConversationAPI.get_conversation_history(conversation_id, limit)
        
        # Transform the response to match frontend expectations
        if result and result.get('messages') and len(result['messages']) > 0:
            # The messages array contains conversation records with 'content' field
            conversation_record = result['messages'][0]  # Get the first (and only) conversation record
            
            # Parse the content field which contains concatenated conversation text
            content_text = conversation_record.get('content', '')
            
            # Convert the concatenated text into structured messages
            messages = []
            if content_text:
                lines = content_text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        if line.startswith('User: '):
                            messages.append({
                                'role': 'user',
                                'content': line[6:],  # Remove 'User: ' prefix
                                'timestamp': conversation_record.get('timestamp')
                            })
                        elif line.startswith('Bot: '):
                            messages.append({
                                'role': 'assistant',
                                'content': line[5:],  # Remove 'Bot: ' prefix
                                'timestamp': conversation_record.get('timestamp')
                            })
                        else:
                            # System message or other format
                            messages.append({
                                'role': 'system',
                                'content': line,
                                'timestamp': conversation_record.get('timestamp')
                            })
            
            # Create the conversation data structure expected by frontend
            # The content field should contain a JSON string with messages array
            formatted_conversation = {
                "conversation_id": conversation_id,
                "timestamp": conversation_record.get('timestamp', datetime.utcnow().isoformat()),
                "content": json.dumps({"messages": messages}),  # JSON string with messages array
                "message_count": len(messages)
            }
            
            return JSONResponse(content={
                "success": True,
                "conversation": [formatted_conversation]
            })
        else:
            # No conversation found
            return JSONResponse(content={
                "success": False,
                "message": f"No conversation found with ID: {conversation_id}"
            })
    except Exception as e:
        logger.error(f"Error in get_conversation_for_viewer: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error retrieving conversation history: {str(e)}"
        }, status_code=500)

app.include_router(chat_history_router)

# Appointment Management API
appointment_router = APIRouter(prefix="/api/appointments", tags=["appointments"])

@appointment_router.get("/")
async def get_client_appointments(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of appointments to retrieve"),
    status: str = Query(None, description="Filter by appointment status"),
    current_user: Dict[str, Any] = Depends(get_current_client_user)
):
    """Get appointments for the authenticated client only."""
    try:
        logger.info(f"Fetching appointments for user: {current_user.get('user', {}).get('email', 'unknown')}")
        from api.config.database import DatabaseContext
        
        client_id = current_user["client"]["id"]
        logger.info(f"Client ID: {client_id}")
        
        # Use sync context manager to avoid event loop issues
        with DatabaseContext('appointments') as collection:
            if not collection:
                logger.error("Database collection not available")
                return JSONResponse(content={
                    "success": False,
                    "error": "Database not available"
                }, status_code=500)
            
            # Build query filter - IMPORTANT: Filter by client_id
            query_filter = {"client_id": client_id}
            if status:
                query_filter["status"] = status
            
            logger.info(f"Query filter: {query_filter}")
            
            # Get appointments sorted by date (newest first) using sync operations
            appointments = list(collection.find(query_filter).sort("appointment_datetime", -1).limit(limit))
            logger.info(f"Found {len(appointments)} appointments")
            
            # Convert ObjectId to string and format ALL datetime fields
            for apt in appointments:
                if "_id" in apt:
                    apt["_id"] = str(apt["_id"])
                # Convert all datetime fields to ISO format strings
                for key, value in apt.items():
                    if isinstance(value, datetime):
                        apt[key] = value.isoformat()
                    elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                        # Handle nested datetime objects in lists/dicts
                        try:
                            if isinstance(value, dict):
                                for nested_key, nested_value in value.items():
                                    if isinstance(nested_value, datetime):
                                        value[nested_key] = nested_value.isoformat()
                            elif isinstance(value, list):
                                for i, item in enumerate(value):
                                    if isinstance(item, datetime):
                                        value[i] = item.isoformat()
                                    elif isinstance(item, dict):
                                        for nested_key, nested_value in item.items():
                                            if isinstance(nested_value, datetime):
                                                item[nested_key] = nested_value.isoformat()
                        except (TypeError, AttributeError):
                            pass  # Skip if not iterable or other issues
            
            return JSONResponse(content={
                "success": True,
                "appointments": appointments,
                "total": len(appointments),
                "client_id": client_id
            })
            
    except Exception as e:
        logger.error(f"Error in get_client_appointments: {str(e)}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "error": f"Error retrieving appointments: {str(e)}"
        }, status_code=500)

@appointment_router.get("/customer/{phone}")
async def get_customer_appointments(
    phone: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of appointments to retrieve")
):
    """Get appointments for a specific customer by phone number."""
    try:
        from api.config.database import DatabaseContext
        
        with DatabaseContext('appointments') as collection:
            if not collection:
                return JSONResponse(content={
                    "success": False,
                    "error": "Database not available"
                }, status_code=500)
            
            # Get customer appointments
            appointments = list(collection.find({
                "customer_phone": phone
            }).sort("appointment_datetime", -1).limit(limit))
            
            # Convert ObjectId to string and format ALL datetime fields
            for apt in appointments:
                apt["_id"] = str(apt["_id"])
                # Convert all datetime fields to ISO format strings
                for key, value in apt.items():
                    if isinstance(value, datetime):
                        apt[key] = value.isoformat()
                    elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                        # Handle nested datetime objects in lists/dicts
                        try:
                            if isinstance(value, dict):
                                for nested_key, nested_value in value.items():
                                    if isinstance(nested_value, datetime):
                                        value[nested_key] = nested_value.isoformat()
                            elif isinstance(value, list):
                                for i, item in enumerate(value):
                                    if isinstance(item, datetime):
                                        value[i] = item.isoformat()
                                    elif isinstance(item, dict):
                                        for nested_key, nested_value in item.items():
                                            if isinstance(nested_value, datetime):
                                                item[nested_key] = nested_value.isoformat()
                        except (TypeError, AttributeError):
                            pass  # Skip if not iterable or other issues
            
            return JSONResponse(content={
                "success": True,
                "appointments": appointments,
                "customer_phone": phone
            })
            
    except Exception as e:
        logger.error(f"Error in get_customer_appointments: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error retrieving customer appointments: {str(e)}"
        }, status_code=500)

@appointment_router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    status_data: dict
):
    """Update appointment status."""
    try:
        from api.config.database import DatabaseContext
        
        new_status = status_data.get("status")
        if new_status not in ["confirmed", "pending", "cancelled", "completed"]:
            return JSONResponse(content={
                "success": False,
                "error": "Invalid status. Must be one of: confirmed, pending, cancelled, completed"
            }, status_code=400)
        
        with DatabaseContext('appointments') as collection:
            if not collection:
                return JSONResponse(content={
                    "success": False,
                    "error": "Database not available"
                }, status_code=500)
            
            result = collection.update_one(
                {"appointment_id": appointment_id},
                {
                    "$set": {
                        "status": new_status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                return JSONResponse(content={
                    "success": True,
                    "message": f"Appointment status updated to {new_status}"
                })
            else:
                return JSONResponse(content={
                    "success": False,
                    "error": "Appointment not found"
                }, status_code=404)
            
    except Exception as e:
        logger.error(f"Error in update_appointment_status: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error updating appointment status: {str(e)}"
        }, status_code=500)

app.include_router(appointment_router)

# RASA Proxy for conversation logging
from .rasa_proxy import router as rasa_proxy_router
app.include_router(rasa_proxy_router)

# Include multi-tenant routes
try:
    from .routes.client_dashboard import router as client_dashboard_router
    from .routes.client_registration import router as client_registration_router
    from .routes.super_admin_routes import router as super_admin_router
    
    app.include_router(client_dashboard_router)
    app.include_router(client_registration_router)
    app.include_router(super_admin_router, prefix="/api/super-admin")
except ImportError as e:
    print(f"[WARNING] Multi-tenant routes not available: {e}")

# Include widget API with proper prefix
try:
    from .widget_api.multi_tenant_chat import router as widget_router
    
    app.include_router(widget_router, prefix="/api/widget")
    print("[OK] Widget API included with prefix /api/widget")
except ImportError as e:
    print(f"[WARNING] Multi-tenant widget API not available: {e}")
except Exception as e:
    print(f"[WARNING] Error setting up widget API: {e}")

# Include streaming chat API
try:
    from .widget_api.streaming_chat import router as streaming_chat_router
    
    app.include_router(streaming_chat_router, prefix="/api/widget")
    print("[OK] Streaming chat API included with prefix /api/widget")
except ImportError as e:
    print(f"[WARNING] Streaming chat API not available: {e}")
except Exception as e:
    print(f"[WARNING] Error setting up streaming chat API: {e}")

# Include cache warming routes
try:
    from .routes.cache_warming import router as cache_warming_router
    
    app.include_router(cache_warming_router)
    print("[OK] Cache warming API included")
except ImportError as e:
    print(f"[WARNING] Cache warming API not available: {e}")
except Exception as e:
    print(f"[WARNING] Error setting up cache warming API: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("BACKEND_PORT", "8000")))
