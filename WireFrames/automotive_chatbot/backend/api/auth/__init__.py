"""Authentication Module

This module provides authentication functionality for the CleverCompanion system,
including client user authentication, JWT token handling, and super admin authentication.
"""

# Client Authentication
from .client_auth import (
    ClientAuthManager,
    get_current_client_user,
    get_current_client_id,
    require_client_admin
)

# JWT Token Handling
from .jwt_handler import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password
)

# Super Admin Authentication
from .super_admin_auth import (
    SuperAdminAuth,
    SUPER_ADMIN_EMAIL,
    SUPER_ADMIN_PASSWORD
)

__all__ = [
    # Client Authentication
    "ClientAuthManager",
    "get_current_client_user",
    "get_current_client_id",
    "require_client_admin",
    
    # JWT Token Handling
    "create_access_token",
    "verify_token",
    "hash_password",
    "verify_password",
    
    # Super Admin Authentication
    "SuperAdminAuth",
    "SUPER_ADMIN_EMAIL",
    "SUPER_ADMIN_PASSWORD"
]