from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from .models import ClientLoginRequest, SuperAdminLoginRequest, ClientRegistrationRequest
from .auth import hash_password, create_access_token

# Try to import MongoDB dependencies (optional)
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    print("[WARN] Motor not available - using mock data for admin features")

admin_router = APIRouter(prefix="/api", tags=["admin"])

# MongoDB connection (optional)
ADMIN_CONNECTION = "mongodb+srv://your-connection-string"
DATABASE_NAME = "automotive_chatbot_saas"
admin_client = None
admin_db = None

@admin_router.post("/auth/client-login")
async def client_login(request: ClientLoginRequest):
    """Client user login endpoint"""
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
                "status": "active"
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

@admin_router.post("/auth/super-admin-login")
async def super_admin_login(request: SuperAdminLoginRequest):
    """Super admin login endpoint"""
    # Mock response for testing
    if request.email == "admin@clevercompanion.com" and request.password == "SuperAdmin123!":
        token_data = {
            "email": request.email,
            "role": "super_admin",
            "type": "super_admin"
        }
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
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

@admin_router.post("/client-registration/register")
async def register_new_client(request: ClientRegistrationRequest):
    """Register a new automotive business client"""
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@admin_router.get("/super-admin/clients")
async def get_all_clients():
    """Get all clients for super admin"""
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
        },
        {
            "id": "client_456",
            "business_name": "Elite Car Dealership",
            "domain": "elitecars.com.sg",
            "contact_email": "contact@elitecars.com.sg",
            "status": "pending",
            "subscription_plan": {
                "plan_type": "basic",
                "price_per_month": 99.0
            },
            "created_at": "2025-01-16T14:20:00Z",
            "current_month_conversations": 0,
            "total_conversations": 0
        }
    ]
    return clients

@admin_router.post("/super-admin/clients/{client_id}/approve")
async def approve_client(client_id: str):
    """Approve a pending client account"""
    return {
        "success": True,
        "message": f"Client {client_id} approved successfully",
        "client_id": client_id
    }

@admin_router.post("/super-admin/clients/{client_id}/suspend")
async def suspend_client(client_id: str):
    """Suspend an active client account"""
    return {
        "success": True,
        "message": f"Client {client_id} suspended successfully",
        "client_id": client_id
    }

@admin_router.get("/super-admin/metrics")
async def get_system_metrics():
    """Get system-wide metrics"""
    return {
        "total_clients": 2,
        "active_clients": 1,
        "pending_approvals": 1,
        "suspended_clients": 0,
        "total_conversations_today": 0,
        "total_conversations_this_month": 0,
        "revenue_this_month": 299.0,
        "system_uptime": 99.9,
        "last_updated": datetime.utcnow().isoformat()
    }

@admin_router.get("/super-admin/clients/{client_id}")
async def get_client_details(client_id: str):
    """Get detailed information about a specific client"""
    # Mock client details
    if client_id == "client_123":
        return {
            "id": client_id,
            "business_name": "ABC Motors Singapore",
            "domain": "abcmotors.com.sg",
            "contact_email": "admin@abcmotors.com.sg",
            "status": "active",
            "subscription_plan": {
                "plan_type": "premium",
                "price_per_month": 299.0,
                "features": ["Unlimited conversations", "Custom branding", "Analytics", "Priority support"]
            },
            "created_at": "2025-01-15T10:30:00Z",
            "last_login": "2025-01-16T09:15:00Z",
            "current_month_conversations": 0,
            "total_conversations": 0,
            "contact_info": {
                "phone": "+65 6123 4567",
                "address": "123 Orchard Road, Singapore 238858"
            },
            "admin_users": [
                {
                    "name": "John Tan",
                    "email": "admin@abcmotors.com.sg",
                    "role": "admin",
                    "last_login": "2025-01-16T09:15:00Z"
                }
            ]
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )