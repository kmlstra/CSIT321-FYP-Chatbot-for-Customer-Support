"""Authentication Models for Multi-tenant SaaS Platform

Defines authentication-related data models for JWT tokens, login requests,
and user authentication responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from bson import ObjectId

class LoginRequest(BaseModel):
    """Base login request model"""
    email: EmailStr
    password: str

class ClientLoginRequest(LoginRequest):
    """Client user login request"""
    pass

class SuperAdminLoginRequest(LoginRequest):
    """Super admin login request"""
    pass

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_info: dict

class ClientRegistrationRequest(BaseModel):
    """Client registration request"""
    business_name: str
    domain: str
    contact_email: EmailStr
    admin_user: dict  # Contains name, email, password
    contact_info: dict = {}
    subscription_plan: str = "basic"

class SuperAdmin(BaseModel):
    """Super admin user model"""
    id: Optional[str] = None
    email: EmailStr
    password_hash: str
    name: str
    role: str = "super_admin"
    status: str = "active"  # active, inactive
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    login_count: int = 0
    
    # Permissions
    permissions: List[str] = [
        "manage_clients",
        "view_analytics", 
        "system_settings",
        "user_management",
        "billing_management"
    ]
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class AuthUser(BaseModel):
    """Authenticated user information"""
    id: str
    email: str
    name: str
    role: str  # super_admin, client_admin, client_manager, client_viewer
    client_id: Optional[str] = None  # Only for client users
    permissions: List[str] = []
    
class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr
    
class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str
    
class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str