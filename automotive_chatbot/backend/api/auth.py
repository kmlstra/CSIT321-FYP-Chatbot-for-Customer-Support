"""
Authentication utilities for FastAPI
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
import os
from datetime import datetime, timedelta

# Security scheme
security = HTTPBearer(auto_error=False)

# Mock user for development (replace with real auth later)
MOCK_USER = {
    "id": "dev_user_123",
    "email": "developer@automotive-chatbot.com",
    "name": "Development User",
    "role": "admin",
    "created_at": datetime.utcnow().isoformat()
}

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user
    For development: returns a mock user
    For production: implement proper JWT validation
    """
    
    # Development mode - return mock user
    if os.getenv("DEBUG", "true").lower() == "true":
        return MOCK_USER
    
    # Production mode - validate JWT token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Validate JWT token (implement your JWT logic here)
        token = credentials.credentials
        secret_key = os.getenv("SECRET_KEY", "development-secret-key")
        
        # For now, just return mock user in production too
        # TODO: Implement proper JWT validation
        return MOCK_USER
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None
    Used for endpoints that work with or without authentication
    """
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# Admin role checker
async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Require admin role for certain endpoints
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user 