"""
Client Authentication System
Handles authentication for client users with proper security
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import hashlib
from datetime import datetime, timedelta
from bson import ObjectId

from ..config.database import get_real_admin_db, get_security_manager

# Security scheme
security = HTTPBearer(auto_error=False)

# JWT Configuration
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

class ClientAuthManager:
    def __init__(self, database, security_manager):
        self.db = database
        self.security_manager = security_manager
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == password_hash
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def authenticate_client_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate client user and return user data with token"""
        try:
            # Find user by email
            user = await self.db.client_users.find_one({"email": email})
            if not user:
                return None
            
            # Verify password
            if not self.verify_password(password, user["password_hash"]):
                return None
            
            # Check if user is active
            if user.get("status") != "active":
                return None
            
            # Get client information
            client = await self.db.clients.find_one({"_id": user["client_id"]})
            if not client or client.get("status") != "active":
                return None
            
            # Update login information
            await self.db.client_users.update_one(
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
            
            access_token = self.create_access_token(token_data)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": JWT_EXPIRATION_HOURS * 3600,
                "user": {
                    "id": str(user["_id"]),
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "client_id": str(user["client_id"]),
                    "permissions": user.get("permissions", [])
                },
                "client": {
                    "id": str(client["_id"]),
                    "business_name": client["business_name"],
                    "domain": client["domain"],
                    "status": client["status"],
                    "settings": client.get("settings", {})
                }
            }
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        try:
            user_id = payload.get("user_id")
            client_id = payload.get("client_id")
            
            if not user_id or not client_id:
                return None
            
            # Get user data
            user = await self.db.client_users.find_one({"_id": ObjectId(user_id)})
            if not user or user.get("status") != "active":
                return None
            
            # Get client data
            client = await self.db.clients.find_one({"_id": ObjectId(client_id)})
            if not client or client.get("status") != "active":
                return None
            
            return {
                "user": {
                    "id": str(user["_id"]),
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "client_id": str(user["client_id"]),
                    "permissions": user.get("permissions", [])
                },
                "client": {
                    "id": str(client["_id"]),
                    "business_name": client["business_name"],
                    "domain": client["domain"],
                    "status": client["status"],
                    "settings": client.get("settings", {})
                }
            }
            
        except Exception as e:
            print(f"Get current user error: {e}")
            return None

# Dependency functions
async def get_current_client_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    database = Depends(get_real_admin_db),
    security_manager = Depends(get_security_manager)
) -> Dict[str, Any]:
    """Get current authenticated client user"""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_manager = ClientAuthManager(database, security_manager)
    user_data = await auth_manager.get_current_user(credentials.credentials)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data

async def get_current_client_id(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
) -> str:
    """Get current client ID from authenticated user"""
    return current_user["client"]["id"]

async def require_client_admin(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
) -> Dict[str, Any]:
    """Require client admin role"""
    if current_user["user"]["role"] not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def require_client_manager(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
) -> Dict[str, Any]:
    """Require client manager or admin role"""
    if current_user["user"]["role"] not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required"
        )
    return current_user

# Super Admin Authentication
async def get_super_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    database = Depends(get_real_admin_db)
) -> Dict[str, Any]:
    """Get current authenticated super admin user"""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_manager = ClientAuthManager(database, None)
    payload = auth_manager.verify_token(credentials.credentials)
    
    if not payload or payload.get("type") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Super admin access required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify super admin exists and is active in database
    try:
        from bson import ObjectId
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        admin = await database.super_admins.find_one({"_id": ObjectId(user_id)})
        if not admin or admin.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Super admin account not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": str(admin["_id"]),
            "email": admin["email"],
            "name": admin["name"],
            "role": "super_admin",
            "type": "super_admin"
        }
        
    except Exception as e:
        print(f"Super admin authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

# API Key Authentication (for widget API)
async def authenticate_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    database = Depends(get_real_admin_db)
) -> Dict[str, Any]:
    """Authenticate using API key for widget requests"""
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Find client by API key
    client = await database.clients.find_one({"api_key": api_key})
    
    if not client or client.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    
    return {
        "id": str(client["_id"]),
        "business_name": client["business_name"],
        "domain": client["domain"],
        "settings": client.get("settings", {})
    }