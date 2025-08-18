from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks, Query, APIRouter, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import os
import json
from datetime import datetime, timedelta
import pytz
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from pathlib import Path

# Import and setup logging configuration
from .config.logging_config import setup_logging

# Import performance monitoring and health check components
from .middleware.performance_middleware import PerformanceMiddleware
from .utils.performance_monitor import performance_monitor
from .services.metrics_collector import MetricsCollector
from .routes.health_routes import router as health_router

# Setup logging before any other imports
setup_logging()

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

# Import unified services
try:
    from .services.conversation_service import unified_conversation_service, MessageType
    from .services.unified_session_manager import UnifiedSessionManager
    
    # Initialize unified session manager
    unified_session_manager = UnifiedSessionManager()
    
    print("[OK] Unified session and conversation services initialized")
except ImportError as e:
    print(f"[WARNING] Unified services not available: {e}")
    unified_session_manager = None
    unified_conversation_service = None

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
    expire = datetime.now(pytz.timezone('Asia/Singapore')) + timedelta(hours=JWT_EXPIRATION_HOURS)
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
            "created_at": datetime.now(pytz.timezone('Asia/Singapore')),
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
        
        # Initialize performance monitoring
        try:
            # Start performance monitoring with alert callbacks
            def performance_alert_callback(severity: str, metric_type: str, value: float, message: str):
                logger.warning(f"Performance Alert [{severity}]: {message}")
            
            performance_monitor.add_alert_callback(performance_alert_callback)
            performance_monitor.start_monitoring()
            print("[OK] Performance monitoring system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize performance monitoring: {e}")
        
        # Database connection established - widget API will use direct endpoints
        print("[OK] Database connection ready for widget API endpoints")
        
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
    
    print("Starting CleverCompanion SaaS Platform v3.0...")
    yield
    
    # Shutdown: Stop performance monitoring and metrics collection
    try:
        performance_monitor.stop_monitoring()
        await metrics_collector.stop_collection()
        print("[OK] Performance monitoring and metrics collection stopped")
    except Exception as e:
        logger.error(f"Error stopping monitoring services: {e}")
    
    # Shutdown: Close MongoDB connections
    await close_database_connection()
    print("Shutting down CleverCompanion SaaS Platform v3.0...")

app = FastAPI(
    title="CleverCompanion SaaS Platform",
    description="Multi-tenant automotive chatbot platform with advanced AI capabilities",
    version="3.0.0",
    lifespan=lifespan
)

# Add performance monitoring middleware
app.add_middleware(PerformanceMiddleware)

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

# Include health check routes
app.include_router(health_router, prefix="/health", tags=["health"])

# Initialize metrics collector
metrics_collector = MetricsCollector()

# Start metrics collection in background
@app.on_event("startup")
async def start_metrics_collection():
    """Start background metrics collection"""
    await metrics_collector.start_collection()

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

# Legacy health check endpoint (kept for backward compatibility)
@app.get("/health")
async def legacy_health_check():
    """Legacy health check endpoint - redirects to new detailed health check"""
    db_status = "connected" if admin_db else "disconnected"
    
    # Get performance summary from performance monitor
    try:
        perf_summary = performance_monitor.get_health_summary()
        performance_status = "healthy" if perf_summary.get("overall_health", 0) > 0.7 else "degraded"
    except Exception:
        performance_status = "unknown"
    
    return {
        "status": "healthy" if db_status == "connected" and performance_status != "degraded" else "degraded",
        "version": "3.0.0",
        "database": db_status,
        "performance": performance_status,
        "services": {
            "api": "running",
            "information_service": "available",
            "coe_service": "available",
            "rag_service": "available" if os.getenv("OPENAI_API_KEY") else "limited"
        },
        "note": "This is a legacy endpoint. Use /health/detailed for comprehensive health information."
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
                "$set": {"last_login": datetime.now(pytz.timezone('Asia/Singapore'))},
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
                "$set": {"last_login": datetime.now(pytz.timezone('Asia/Singapore'))},
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
            "created_at": datetime.now(pytz.timezone('Asia/Singapore')),
            "updated_at": datetime.now(pytz.timezone('Asia/Singapore')),
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
            "created_at": datetime.now(pytz.timezone('Asia/Singapore')),
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
                    "activated_at": datetime.now(pytz.timezone('Asia/Singapore')),
                    "updated_at": datetime.now(pytz.timezone('Asia/Singapore'))
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
        
        # Count conversations today - Use Singapore timezone to prevent data accumulating in yesterday
        import pytz
        singapore_tz = pytz.timezone('Asia/Singapore')
        today_sg = datetime.now(singapore_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        conversations_today = await admin_db.conversations.count_documents({
            "created_at": {"$gte": today_sg}
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
            "timestamp": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
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
            "timestamp": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
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
    # Return hardcoded sample data for frontend compatibility
    sample_conversations = [
        {
            "id": "conv_001",
            "timestamp": "2024-01-15T10:30:00+08:00",
            "content": '{"messages": [{"role": "user", "content": "Hello, I need help with my car"}, {"role": "assistant", "content": "Hello! I\'d be happy to help you with your car. What specific issue are you experiencing?"}]}',
            "message_count": 2
        },
        {
            "id": "conv_002",
            "timestamp": "2024-01-15T14:20:00+08:00",
            "content": '{"messages": [{"role": "user", "content": "I want to book a service appointment"}, {"role": "assistant", "content": "I can help you book a service appointment. What type of service do you need?"}]}',
            "message_count": 2
        }
    ]
    
    return JSONResponse(content={
        "success": True,
        "conversations": sample_conversations[:limit]
    })

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
                "timestamp": conversation_record.get('timestamp', datetime.now(pytz.timezone('Asia/Singapore')).isoformat()),
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
            # First get appointments without sorting by appointment_datetime (since it might not exist)
            appointments = list(collection.find(query_filter).limit(limit))
            logger.info(f"Found {len(appointments)} appointments")
            
            # Convert ObjectId to string and create appointment_datetime from date/time fields
            for apt in appointments:
                if "_id" in apt:
                    apt["_id"] = str(apt["_id"])
                # Ensure appointment_id is available - use existing appointment_id or fallback to _id
                if "appointment_id" not in apt or not apt["appointment_id"]:
                    apt["appointment_id"] = str(apt["_id"])
                
                # Create appointment_datetime from appointment_date and appointment_time if they exist
                if "appointment_date" in apt and "appointment_time" in apt and apt["appointment_date"] and apt["appointment_time"]:
                    try:
                        from datetime import datetime as dt
                        # Parse date and time strings
                        date_str = apt["appointment_date"]  # Format: "2025-09-03"
                        time_str = apt["appointment_time"]  # Format: "12:00" or "16:15"
                        
                        # Combine date and time into datetime object
                        datetime_str = f"{date_str} {time_str}"
                        # Use correct format for parsing - date is YYYY-MM-DD, time is HH:MM
                        appointment_dt = dt.strptime(datetime_str, "%Y-%m-%d %H:%M")
                        
                        # Set timezone to Singapore
                        singapore_tz = pytz.timezone('Asia/Singapore')
                        appointment_dt = singapore_tz.localize(appointment_dt)
                        
                        # Store as ISO string for frontend
                        apt["appointment_datetime"] = appointment_dt.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to create appointment_datetime for appointment {apt.get('_id')}: {e}")
                        logger.warning(f"Date: '{apt.get('appointment_date')}', Time: '{apt.get('appointment_time')}'")
                        apt["appointment_datetime"] = None
                else:
                    apt["appointment_datetime"] = None
                
                # Convert all other datetime fields to ISO format strings
                for key, value in apt.items():
                    if isinstance(value, datetime) and key != "appointment_datetime":
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
            
            # Sort appointments by appointment_datetime (newest first)
            appointments.sort(key=lambda x: x.get("appointment_datetime") or "", reverse=True)
            

            
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
            }).limit(limit))
            
            # Convert ObjectId to string and create appointment_datetime from date/time fields
            for apt in appointments:
                apt["_id"] = str(apt["_id"])
                # Ensure appointment_id is available - use existing appointment_id or fallback to _id
                if "appointment_id" not in apt or not apt["appointment_id"]:
                    apt["appointment_id"] = str(apt["_id"])
                
                # Create appointment_datetime from appointment_date and appointment_time if they exist
                if "appointment_date" in apt and "appointment_time" in apt and apt["appointment_date"] and apt["appointment_time"]:
                    try:
                        from datetime import datetime as dt
                        # Parse date and time strings
                        date_str = apt["appointment_date"]  # Format: "2025-09-03"
                        time_str = apt["appointment_time"]  # Format: "12:00" or "16:15"
                        
                        # Combine date and time into datetime object
                        datetime_str = f"{date_str} {time_str}"
                        # Use correct format for parsing - date is YYYY-MM-DD, time is HH:MM
                        appointment_dt = dt.strptime(datetime_str, "%Y-%m-%d %H:%M")
                        
                        # Set timezone to Singapore
                        singapore_tz = pytz.timezone('Asia/Singapore')
                        appointment_dt = singapore_tz.localize(appointment_dt)
                        
                        # Store as ISO string for frontend
                        apt["appointment_datetime"] = appointment_dt.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to create appointment_datetime for appointment {apt.get('_id')}: {e}")
                        logger.warning(f"Date: '{apt.get('appointment_date')}', Time: '{apt.get('appointment_time')}'")
                        apt["appointment_datetime"] = None
                else:
                    apt["appointment_datetime"] = None
                
                # Convert all other datetime fields to ISO format strings
                for key, value in apt.items():
                    if isinstance(value, datetime) and key != "appointment_datetime":
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
            
            # Sort appointments by appointment_datetime (newest first)
            appointments.sort(key=lambda x: x.get("appointment_datetime") or "", reverse=True)
            
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

# Simple appointment booking endpoint
@appointment_router.post("/book")
async def book_appointment(
    appointment_data: dict
):
    """Simple appointment booking - no complex validation, just save to database."""
    try:
        from api.config.database import DatabaseContext
        import uuid
        
        # Extract basic required fields
        service_type = appointment_data.get("service_type", "General Inquiry")
        customer_name = appointment_data.get("customer_name", "")
        customer_phone = appointment_data.get("customer_phone", "")
        preferred_datetime = appointment_data.get("preferred_datetime", "")
        notes = appointment_data.get("notes", "")
        
        # Basic validation - only check if name and phone are provided
        if not customer_name or not customer_phone:
            return JSONResponse(content={
                "success": False,
                "error": "Customer name and phone number are required"
            }, status_code=400)
        
        # Create simple appointment document
        appointment_id = str(uuid.uuid4())[:8]  # Short ID for easy reference
        appointment_doc = {
            "appointment_id": appointment_id,
            "service_type": service_type,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "preferred_datetime": preferred_datetime,
            "notes": notes,
            "status": "pending",
            "created_at": datetime.now(pytz.timezone('Asia/Singapore')),
            "client_id": "default"  # For now, use default client
        }
        
        # Save to database
        with DatabaseContext('appointments') as collection:
            if not collection:
                return JSONResponse(content={
                    "success": False,
                    "error": "Database not available"
                }, status_code=500)
            
            result = collection.insert_one(appointment_doc)
            
            if result.inserted_id:
                return JSONResponse(content={
                    "success": True,
                    "message": "Appointment booked successfully!",
                    "appointment_id": appointment_id,
                    "data": {
                        "service_type": service_type,
                        "customer_name": customer_name,
                        "preferred_datetime": preferred_datetime,
                        "status": "pending"
                    }
                })
            else:
                return JSONResponse(content={
                    "success": False,
                    "error": "Failed to save appointment"
                }, status_code=500)
            
    except Exception as e:
        logger.error(f"Error in book_appointment: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error booking appointment: {str(e)}"
        }, status_code=500)

@appointment_router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    status_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_client_user)
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
            
            # Get client_id from authenticated user
            client_id = current_user["client"]["id"]
            
            # Try to update using appointment_id first, then fallback to _id
            from bson import ObjectId
            
            # Prepare query conditions
            query_conditions = [{"appointment_id": appointment_id}]
            
            # Try to convert to ObjectId for _id field if it's a valid ObjectId string
            try:
                if ObjectId.is_valid(appointment_id):
                    query_conditions.append({"_id": ObjectId(appointment_id)})
            except:
                pass
            
            # Prepare update data with timestamp
            current_time = datetime.now(pytz.timezone('Asia/Singapore'))
            update_data = {
                "status": new_status,
                "updated_at": current_time
            }
            
            # Add specific timestamp fields for cancelled and completed status
            if new_status == "cancelled":
                update_data["cancelled_time"] = current_time
            elif new_status == "completed":
                update_data["completed_time"] = current_time
            
            result = collection.update_one(
                {
                    "$or": query_conditions,
                    "client_id": client_id
                },
                {
                    "$set": update_data
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

# Conversation storage endpoint for widget
@app.post("/api/conversations/store")
async def store_conversation(
    conversation_data: dict
):
    """Store conversation data from the widget using unified conversation service"""
    try:
        # Extract required fields from conversation data
        session_id = conversation_data.get("session_id")
        message = conversation_data.get("message", "")
        message_type_str = conversation_data.get("message_type", "user")
        client_id = conversation_data.get("client_id")
        metadata = conversation_data.get("metadata", {})
        
        # Validate required fields
        if not session_id:
            return JSONResponse(content={
                "success": False,
                "error": "session_id is required"
            }, status_code=400)
        
        # Map message type to MessageType enum
        try:
            if message_type_str.lower() == "user":
                message_type = MessageType.USER
            elif message_type_str.lower() == "assistant" or message_type_str.lower() == "bot":
                message_type = MessageType.ASSISTANT
            elif message_type_str.lower() == "system":
                message_type = MessageType.SYSTEM
            else:
                message_type = MessageType.USER  # Default to user
        except:
            message_type = MessageType.USER
        
        # Store message using unified conversation service
        success = unified_conversation_service.store_message(
            session_id=session_id,
            message=message,
            message_type=message_type,
            metadata=metadata,
            client_id=client_id
        )
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Conversation stored successfully",
                "session_id": session_id
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": "Failed to store conversation"
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"Error storing conversation: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error storing conversation: {str(e)}"
        }, status_code=500)

# Client configuration endpoint for widget
@app.get("/api/config/{client_id}")
async def get_client_config(client_id: str):
    """Get client configuration for the widget"""
    try:
        global admin_db
        if not admin_db:
            return JSONResponse(content={
                "success": False,
                "error": "Database not available"
            }, status_code=500)
        
        # Find client configuration
        client = await admin_db.clients.find_one({"client_id": client_id})
        
        if not client:
            # Return default configuration if client not found
            default_config = {
                "client_id": client_id,
                "branding": {
                    "logo_url": "/static/media/images/CleverCompanion-logo.png",
                    "company_name": "CleverCompanion",
                    "primary_color": "#007bff",
                    "secondary_color": "#6c757d"
                },
                "features": {
                    "coe_prices": True,
                    "appointment_booking": True,
                    "loan_calculator": True,
                    "live_support": True
                },
                "contact_info": {
                    "phone": "+65 6123 4567",
                    "email": "support@clevercompanion.com",
                    "address": "Singapore"
                }
            }
            return JSONResponse(content=default_config)
        
        # Return client configuration
        settings = client.get("settings", {})
        config = {
            "client_id": client.get("client_id", client_id),
            "branding": settings.get("branding", {}),
            "features": settings.get("features", {}),
            "contact_info": settings.get("contact_info", {})
        }
        
        return JSONResponse(content=config)
        
    except Exception as e:
        logger.error(f"Error getting client config: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error getting client config: {str(e)}"
        }, status_code=500)

# Widget-specific client configuration endpoint (duplicate of /api/config/{client_id})
@app.get("/api/widget/config/{client_id}")
async def get_widget_client_config(client_id: str):
    """Get client configuration for the widget - same as /api/config/{client_id}"""
    try:
        global admin_db
        if not admin_db:
            return JSONResponse(content={
                "success": False,
                "error": "Database not available"
            }, status_code=500)
        
        # Find client configuration
        client = await admin_db.clients.find_one({"client_id": client_id})
        
        if not client:
            # Return default configuration if client not found
            default_config = {
                "client_id": client_id,
                "branding": {
                    "logo_url": "/static/media/images/CleverCompanion-logo.png",
                    "company_name": "CleverCompanion",
                    "primary_color": "#007bff",
                    "secondary_color": "#6c757d"
                },
                "features": {
                    "coe_prices": True,
                    "appointment_booking": True,
                    "loan_calculator": True,
                    "live_support": True
                },
                "contact_info": {
                    "phone": "+65 6123 4567",
                    "email": "support@clevercompanion.com",
                    "address": "Singapore"
                }
            }
            return JSONResponse(content=default_config)
        
        # Return client configuration
        settings = client.get("settings", {})
        config = {
            "client_id": client.get("client_id", client_id),
            "branding": settings.get("branding", {}),
            "features": settings.get("features", {}),
            "contact_info": settings.get("contact_info", {})
        }
        
        return JSONResponse(content=config)
        
    except Exception as e:
        logger.error(f"Error getting widget client config: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": f"Error getting widget client config: {str(e)}"
        }, status_code=500)

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

# Widget API functionality now integrated directly into main endpoints
print("[OK] Widget API endpoints integrated directly into main application")

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

# Widget-specific conversation store endpoint (duplicate of /api/conversations/store)
@app.post("/api/widget/conversations/store")
async def store_widget_conversation(
    conversation_data: dict,
    client_domain: Optional[str] = Header(None, alias="X-Client-Domain"),
    origin: Optional[str] = Header(None)
):
    """Store conversation data from widget using unified conversation service"""
    try:
        # Extract required fields from conversation data
        session_id = conversation_data.get("session_id")
        message = conversation_data.get("message", "")
        message_type_str = conversation_data.get("message_type", "user")
        client_id = conversation_data.get("client_id")
        metadata = conversation_data.get("metadata", {})
        
        # Extract domain from origin if not provided
        if not client_domain and origin:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(origin)
                client_domain = parsed.netloc
            except:
                pass
        
        # Validate required fields
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        if not client_id and not client_domain:
            raise HTTPException(status_code=400, detail="client_id or client domain is required")
        
        # Add client domain to metadata if available
        if client_domain:
            metadata["client_domain"] = client_domain
        
        # Use client_domain as client_id if client_id not provided
        if not client_id and client_domain:
            client_id = client_domain
        
        # Map message type to MessageType enum
        try:
            if message_type_str.lower() == "user":
                message_type = MessageType.USER
            elif message_type_str.lower() == "assistant" or message_type_str.lower() == "bot":
                message_type = MessageType.ASSISTANT
            elif message_type_str.lower() == "system":
                message_type = MessageType.SYSTEM
            else:
                message_type = MessageType.USER  # Default to user
        except:
            message_type = MessageType.USER
        
        # Store message using unified conversation service
        success = unified_conversation_service.store_message(
            session_id=session_id,
            message=message,
            message_type=message_type,
            metadata=metadata,
            client_id=client_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Conversation stored successfully",
                "session_id": session_id,
                "timestamp": datetime.now(pytz.timezone('Asia/Singapore')).isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to store conversation data"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing widget conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store conversation data"
        )

# ============================================================================
# UNIFIED SESSION AND CONVERSATION MANAGEMENT API ENDPOINTS
# ============================================================================
# These new endpoints provide unified session and conversation management
# while maintaining full backward compatibility with existing endpoints.
# The existing /api/config/{client_id} and /api/conversations/store endpoints
# remain completely unchanged to ensure widget compatibility.

# This section will be moved to earlier in the file

# Unified session management endpoints
@app.post("/api/unified/sessions/create")
async def create_unified_session(
    session_data: dict
):
    """Create a new unified session with both session_id and conversation_id"""
    try:
        if not unified_session_manager:
            raise HTTPException(
                status_code=503,
                detail="Unified session manager not available"
            )
        
        # Validate required fields
        client_id = session_data.get("client_id")
        user_id = session_data.get("user_id", "anonymous")
        if not client_id:
            raise HTTPException(status_code=400, detail="client_id is required")
        
        # Create new unified session
        session_id, conversation_id = unified_session_manager.create_session(
            client_id=client_id,
            user_id=user_id,
            metadata=session_data.get("metadata", {})
        )
        
        session_info = {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "client_id": client_id
        }
        
        return {
            "success": True,
            "session": session_info,
            "message": "Unified session created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating unified session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create unified session"
        )

@app.get("/api/unified/sessions/{session_id}")
async def get_unified_session(session_id: str):
    """Get unified session information"""
    try:
        if not unified_session_manager:
            raise HTTPException(
                status_code=503,
                detail="Unified session manager not available"
            )
        
        session_info = unified_session_manager.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "session": session_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unified session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get unified session"
        )

@app.post("/api/unified/sessions/{session_id}/extend")
async def extend_unified_session(session_id: str):
    """Extend unified session expiry time"""
    try:
        if not unified_session_manager:
            raise HTTPException(
                status_code=503,
                detail="Unified session manager not available"
            )
        
        success = unified_session_manager.extend_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        return {
            "success": True,
            "message": "Session extended successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending unified session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extend unified session"
        )

# Unified conversation management endpoints
@app.post("/api/unified/conversations/store")
async def store_unified_conversation(
    conversation_data: dict
):
    """Store conversation message using unified conversation service"""
    try:
        if not unified_conversation_service:
            raise HTTPException(
                status_code=503,
                detail="Unified conversation service not available"
            )
        
        # Validate required fields
        session_id = conversation_data.get("session_id")
        message = conversation_data.get("message")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        if not message:
            raise HTTPException(status_code=400, detail="message is required")
        
        # Determine message type
        message_type_str = conversation_data.get("message_type", "user").lower()
        
        # Map message type string to MessageType enum
        if message_type_str == "user":
            message_type = MessageType.USER
        elif message_type_str in ["bot", "assistant"]:
            message_type = MessageType.ASSISTANT
        elif message_type_str == "system":
            message_type = MessageType.SYSTEM
        else:
            message_type = MessageType.USER  # Default to user
        
        # Store conversation message
        result = unified_conversation_service.store_message(
            session_id=session_id,
            message=message,
            message_type=message_type,
            metadata=conversation_data.get("metadata", {})
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to store message"
            )
        
        return {
            "success": True,
            "message": "Conversation stored successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing unified conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store unified conversation"
        )

@app.get("/api/unified/conversations/{conversation_id}/history")
async def get_unified_conversation_history(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0
):
    """Get conversation history using unified conversation service"""
    try:
        if not unified_conversation_service:
            raise HTTPException(
                status_code=503,
                detail="Unified conversation service not available"
            )
        
        history = unified_conversation_service.get_conversation_history_by_id(
            conversation_id=conversation_id,
            limit=limit,
            include_metadata=True
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": history,
            "total_messages": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unified conversation history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get unified conversation history"
        )

@app.get("/api/unified/conversations/client/{client_id}")
async def get_client_unified_conversations(
    client_id: str,
    limit: int = 20,
    offset: int = 0
):
    """Get all conversations for a specific client using unified service"""
    try:
        if not unified_conversation_service:
            raise HTTPException(
                status_code=503,
                detail="Unified conversation service not available"
            )
        
        conversations = unified_conversation_service.get_client_conversations(
            client_id=client_id,
            limit=limit,
            include_archived=False
        )
        
        return {
            "success": True,
            "client_id": client_id,
            "conversations": conversations,
            "total_conversations": len(conversations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client unified conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get client unified conversations"
        )

# Unified statistics and management endpoints
@app.get("/api/unified/stats/sessions")
async def get_unified_session_stats():
    """Get unified session statistics"""
    try:
        if not unified_session_manager:
            raise HTTPException(
                status_code=503,
                detail="Unified session manager not available"
            )
        
        stats = unified_session_manager.get_session_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unified session stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get unified session stats"
        )

@app.get("/api/unified/stats/conversations")
async def get_unified_conversation_stats():
    """Get unified conversation statistics"""
    try:
        if not unified_conversation_service:
            raise HTTPException(
                status_code=503,
                detail="Unified conversation service not available"
            )
        
        stats = unified_conversation_service.get_conversation_statistics()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unified conversation stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get unified conversation stats"
        )

@app.post("/api/unified/cleanup/expired")
async def cleanup_unified_expired_data():
    """Cleanup expired sessions and old conversations"""
    try:
        if not unified_session_manager or not unified_conversation_service:
            raise HTTPException(
                status_code=503,
                detail="Unified services not available"
            )
        
        # Cleanup expired sessions
        session_cleanup_result = unified_session_manager.cleanup_expired_sessions()
        
        # Cleanup old conversations (older than 90 days)
        conversation_cleanup_result = unified_conversation_service.cleanup_old_conversations(days_old=90)
        
        return {
            "success": True,
            "cleanup_results": {
                "expired_sessions_removed": session_cleanup_result,
                "old_conversations_removed": conversation_cleanup_result
            },
            "message": "Cleanup completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during unified cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup unified data"
        )

# Backward compatibility endpoints - these mirror existing functionality
# but use the unified services internally for consistency
@app.post("/api/unified/legacy/conversations/store")
async def store_legacy_compatible_conversation(
    conversation_data: dict
):
    """Legacy-compatible conversation storage using unified services"""
    try:
        if not unified_conversation_service or not unified_session_manager:
            # Fallback to original behavior if unified services not available
            return await store_conversation(conversation_data)
        
        # Extract session_id or create new session if needed
        session_id = conversation_data.get("session_id")
        client_id = conversation_data.get("client_id")
        
        if not session_id and client_id:
            # Create new session for legacy compatibility
            session_info = await unified_session_manager.create_session(
                client_id=client_id,
                metadata=conversation_data.get("metadata", {})
            )
            session_id = session_info["session_id"]
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id or client_id is required")
        
        # Store using unified service
        result = await unified_conversation_service.store_message(
            session_id=session_id,
            message=conversation_data.get("message", conversation_data),
            metadata=conversation_data.get("metadata", {})
        )
        
        # Return in legacy format
        return {
            "success": True,
            "message": "Conversation stored successfully",
            "conversation_id": result["conversation_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing legacy compatible conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store legacy compatible conversation"
        )

# Chat unified endpoint - handles chat requests with automatic conversation storage
@app.post("/api/chat/unified")
async def chat_unified(
    request_data: dict,
    request: Request
):
    """Unified chat endpoint that processes messages and stores conversations automatically"""
    try:
        # Import chat handler
        from api.widget_api.multi_tenant_chat import ChatRequest, get_chat_handler
        from api.services.conversation_service import MessageType
        
        # Extract request data
        message = request_data.get("message", "")
        session_id = request_data.get("session_id")
        client_id = request_data.get("client_id")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        # Get database connection
        from api.config.database import get_real_admin_db
        db = await get_real_admin_db()
        
        if db is None:
            raise HTTPException(
                status_code=503, 
                detail="Database not available. Please try again in a moment."
            )
        
        # Ensure session exists (handles frontend-generated session IDs)
        if unified_session_manager:
            try:
                session_id, conversation_id = unified_session_manager.ensure_session_exists(
                    session_id=session_id,
                    client_id=client_id,
                    user_id=request_data.get("user_info", {}).get("user_id")
                )
                logger.info(f"[UNIFIED_CHAT] Session ensured - session_id: {session_id}, conversation_id: {conversation_id}")
            except Exception as e:
                logger.error(f"[UNIFIED_CHAT] Failed to ensure session {session_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to ensure session: {e}")
        
        # Store user message first
        if unified_conversation_service:
            user_metadata = {
                'timestamp': datetime.now(pytz.timezone('Asia/Singapore')).isoformat(),
                'source': 'chat_unified',
                'user_info': request_data.get("user_info", {}),
                'client_domain': request.headers.get('X-Client-Domain', 'unknown')
            }
            
            unified_conversation_service.store_message(
                session_id=session_id,
                message=message,
                message_type=MessageType.USER,
                metadata=user_metadata,
                client_id=client_id
            )
        
        # Get chat handler and process request
        handler = get_chat_handler(db)
        
        # Create chat request
        chat_request = ChatRequest(
            message=message,
            session_id=session_id,
            client_id=client_id,
            user_info=request_data.get("user_info", {})
        )
        
        # Process chat request
        response = await handler.process_chat_request(chat_request)
        
        # Store bot response
        if unified_conversation_service:
            bot_metadata = {
                'timestamp': response.timestamp.isoformat(),
                'source': 'rasa_response',
                'response_metadata': response.metadata
            }
            
            unified_conversation_service.store_message(
                session_id=session_id,
                message=response.response,
                message_type=MessageType.ASSISTANT,
                metadata=bot_metadata,
                client_id=client_id
            )
        
        return {
            "success": True,
            "response": response.response,
            "session_id": response.session_id,
            "client_id": response.client_id,
            "timestamp": response.timestamp.isoformat(),
            "metadata": response.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process chat request"
        )

# Unified chat endpoint - alias for the above endpoint
@app.post("/api/unified/chat")
async def unified_chat(
    request_data: dict,
    request: Request
):
    """Unified chat endpoint - alias for /api/chat/unified"""
    return await chat_unified(request_data, request)

print("[OK] Unified session and conversation management API endpoints added")
print("[OK] Unified chat endpoint /api/chat/unified added")
print("[INFO] All existing endpoints remain unchanged for backward compatibility")
print("[INFO] Client configuration endpoint /api/config/{client_id} is fully preserved")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("BACKEND_PORT", "8000")))
