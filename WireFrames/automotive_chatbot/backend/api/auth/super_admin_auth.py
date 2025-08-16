"""
Super Admin Authentication
Creates the initial super admin user and handles super admin login
"""

import hashlib
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any, Optional
from .jwt_handler import create_access_token

# Super Admin Credentials (change in production)
SUPER_ADMIN_EMAIL = "admin@clevercompanion.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin123!"

class SuperAdminAuth:
    def __init__(self, database):
        self.db = database
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    async def create_super_admin(self):
        """Create initial super admin user"""
        try:
            # Check if super admin already exists
            existing_admin = await self.db.super_admins.find_one({"email": SUPER_ADMIN_EMAIL})
            if existing_admin:
                print("✅ Super admin already exists")
                return True
            
            # Create super admin user
            super_admin = {
                "email": SUPER_ADMIN_EMAIL,
                "password_hash": self.hash_password(SUPER_ADMIN_PASSWORD),
                "name": "Super Administrator",
                "role": "super_admin",
                "status": "active",
                "created_at": datetime.now(pytz.timezone('Asia/Singapore')),
                "last_login": None,
                "login_count": 0,
                "permissions": [
                    "manage_all_clients",
                    "approve_accounts",
                    "view_system_metrics",
                    "manage_billing",
                    "system_administration"
                ]
            }
            
            await self.db.super_admins.insert_one(super_admin)
            print(f"✅ Created super admin: {SUPER_ADMIN_EMAIL}")
            print(f"🔑 Super admin password: {SUPER_ADMIN_PASSWORD}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create super admin: {e}")
            return False
    
    async def authenticate_super_admin(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate super admin user"""
        try:
            # Find super admin by email
            admin = await self.db.super_admins.find_one({"email": email})
            if not admin:
                return None
            
            # Verify password
            if self.hash_password(password) != admin["password_hash"]:
                return None
            
            # Check if admin is active
            if admin.get("status") != "active":
                return None
            
            # Update login info
            await self.db.super_admins.update_one(
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
                    "role": "super_admin",
                    "permissions": admin.get("permissions", [])
                }
            }
            
        except Exception as e:
            print(f"Super admin authentication error: {e}")
            return None