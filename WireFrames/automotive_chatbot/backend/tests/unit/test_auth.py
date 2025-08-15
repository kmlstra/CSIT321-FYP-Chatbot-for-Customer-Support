#!/usr/bin/env python3
"""
Unit tests for authentication endpoints
"""

import pytest
import jwt
from datetime import datetime, timedelta
from fastapi import status
from unittest.mock import patch, AsyncMock
import hashlib

# Test data
VALID_CLIENT_LOGIN = {
    "email": "john@abcmotors.com",
    "password": "ABCMotors123!"
}

VALID_SUPER_ADMIN_LOGIN = {
    "email": "admin@clevercompanion.com",
    "password": "SuperAdmin123!"
}

INVALID_LOGIN = {
    "email": "invalid@example.com",
    "password": "wrongpassword"
}

@pytest.mark.unit
@pytest.mark.auth
class TestClientAuthentication:
    """Test client user authentication"""
    
    async def test_client_login_success(self, async_client, test_client_with_user):
        """Test successful client login"""
        client_data = test_client_with_user
        
        login_data = {
            "email": client_data["user_data"]["email"],
            "password": "ABCMotors123!"  # Original password
        }
        
        response = await async_client.post("/api/auth/client-login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert "client" in data
        
        # Verify token type
        assert data["token_type"] == "bearer"
        
        # Verify user data
        user = data["user"]
        assert user["email"] == login_data["email"]
        assert user["role"] == "admin"
        assert "id" in user
        assert "client_id" in user
        
        # Verify client data
        client = data["client"]
        assert client["business_name"] == "ABC Motors"
        assert client["domain"] == "abcmotors.com"
        assert client["status"] == "active"
        
        # Verify JWT token
        token = data["access_token"]
        decoded = jwt.decode(token, "your-super-secret-jwt-key-change-in-production", algorithms=["HS256"])
        assert decoded["email"] == login_data["email"]
        assert decoded["type"] == "client_user"
    
    async def test_client_login_invalid_email(self, async_client):
        """Test client login with invalid email"""
        response = await async_client.post("/api/auth/client-login", json=INVALID_LOGIN)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid email or password" in data["detail"]
    
    async def test_client_login_invalid_password(self, async_client, test_client_with_user):
        """Test client login with invalid password"""
        client_data = test_client_with_user
        
        login_data = {
            "email": client_data["user_data"]["email"],
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/auth/client-login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid email or password" in data["detail"]
    
    async def test_client_login_inactive_user(self, async_client, test_db, abc_motors_data):
        """Test client login with inactive user"""
        # Create inactive client and user
        from conftest import hash_password
        import secrets
        
        # Create client
        client_data = {
            "business_name": abc_motors_data["business_name"],
            "domain": abc_motors_data["domain"],
            "contact_email": abc_motors_data["contact_email"],
            "status": "active",
            "api_key": f"cc_{secrets.token_urlsafe(32)}",
            "created_at": datetime.utcnow()
        }
        
        client_result = await test_db.clients.insert_one(client_data)
        client_id = str(client_result.inserted_id)
        
        # Create inactive user
        user_data = {
            "client_id": client_id,
            "name": abc_motors_data["admin_user"]["name"],
            "email": abc_motors_data["admin_user"]["email"],
            "password_hash": hash_password(abc_motors_data["admin_user"]["password"]),
            "role": "admin",
            "status": "inactive",  # Inactive status
            "created_at": datetime.utcnow()
        }
        
        await test_db.client_users.insert_one(user_data)
        
        login_data = {
            "email": abc_motors_data["admin_user"]["email"],
            "password": abc_motors_data["admin_user"]["password"]
        }
        
        response = await async_client.post("/api/auth/client-login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Account is not active" in data["detail"]
    
    async def test_client_login_missing_fields(self, async_client):
        """Test client login with missing fields"""
        # Missing password
        response = await async_client.post("/api/auth/client-login", json={"email": "test@example.com"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing email
        response = await async_client.post("/api/auth/client-login", json={"password": "password"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Empty request
        response = await async_client.post("/api/auth/client-login", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.unit
@pytest.mark.auth
class TestSuperAdminAuthentication:
    """Test super admin authentication"""
    
    async def test_super_admin_login_success(self, async_client, super_admin_token, test_db):
        """Test successful super admin login"""
        login_data = {
            "email": "admin@clevercompanion.com",
            "password": "SuperAdmin123!"
        }
        
        response = await async_client.post("/api/auth/super-admin-login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        
        # Verify token type
        assert data["token_type"] == "bearer"
        
        # Verify user data
        user = data["user"]
        assert user["email"] == "admin@clevercompanion.com"
        assert user["role"] == "super_admin"
        assert "id" in user
        
        # Verify JWT token
        token = data["access_token"]
        decoded = jwt.decode(token, "your-super-secret-jwt-key-change-in-production", algorithms=["HS256"])
        assert decoded["email"] == "admin@clevercompanion.com"
        assert decoded["type"] == "super_admin"
    
    async def test_super_admin_login_invalid_credentials(self, async_client):
        """Test super admin login with invalid credentials"""
        response = await async_client.post("/api/auth/super-admin-login", json=INVALID_LOGIN)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid email or password" in data["detail"]
    
    async def test_super_admin_login_inactive_admin(self, async_client, test_db):
        """Test super admin login with inactive admin"""
        from conftest import hash_password
        
        # Create inactive super admin
        admin_data = {
            "email": "inactive@clevercompanion.com",
            "password_hash": hash_password("InactiveAdmin123!"),
            "name": "Inactive Administrator",
            "role": "super_admin",
            "status": "inactive",  # Inactive status
            "created_at": datetime.utcnow()
        }
        
        await test_db.super_admins.insert_one(admin_data)
        
        login_data = {
            "email": "inactive@clevercompanion.com",
            "password": "InactiveAdmin123!"
        }
        
        response = await async_client.post("/api/auth/super-admin-login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Account is not active" in data["detail"]

@pytest.mark.unit
@pytest.mark.auth
class TestAuthenticationHelpers:
    """Test authentication helper functions"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = hashlib.sha256(password.encode()).hexdigest()
        
        # Test consistency
        assert hashlib.sha256(password.encode()).hexdigest() == hashed
        
        # Test different passwords produce different hashes
        different_password = "DifferentPassword123!"
        different_hash = hashlib.sha256(different_password.encode()).hexdigest()
        assert hashed != different_hash
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        from conftest import create_access_token
        
        token_data = {
            "user_id": "test_user_id",
            "email": "test@example.com",
            "role": "admin",
            "type": "client_user"
        }
        
        token = create_access_token(token_data)
        
        # Verify token can be decoded
        decoded = jwt.decode(token, "your-super-secret-jwt-key-change-in-production", algorithms=["HS256"])
        
        assert decoded["user_id"] == "test_user_id"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "admin"
        assert decoded["type"] == "client_user"
        assert "exp" in decoded
        
        # Verify expiration is in the future
        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        assert exp_time > datetime.utcnow()
    
    def test_token_expiration(self):
        """Test token expiration"""
        from conftest import create_access_token
        
        token_data = {"user_id": "test"}
        token = create_access_token(token_data)
        
        decoded = jwt.decode(token, "your-super-secret-jwt-key-change-in-production", algorithms=["HS256"])
        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        
        # Should expire in approximately 24 hours
        expected_exp = datetime.utcnow() + timedelta(hours=24)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        
        # Allow 60 seconds tolerance
        assert time_diff < 60

@pytest.mark.unit
@pytest.mark.auth
class TestAuthenticationEdgeCases:
    """Test authentication edge cases and error handling"""
    
    async def test_malformed_json_request(self, async_client):
        """Test authentication with malformed JSON"""
        response = await async_client.post(
            "/api/auth/client-login",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_empty_string_credentials(self, async_client):
        """Test authentication with empty string credentials"""
        login_data = {
            "email": "",
            "password": ""
        }
        
        response = await async_client.post("/api/auth/client-login", json=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_sql_injection_attempt(self, async_client):
        """Test authentication with SQL injection attempt"""
        login_data = {
            "email": "admin@example.com'; DROP TABLE users; --",
            "password": "password"
        }
        
        response = await async_client.post("/api/auth/client-login", json=login_data)
        
        # Should return unauthorized, not cause an error
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_very_long_credentials(self, async_client):
        """Test authentication with very long credentials"""
        long_string = "a" * 10000
        
        login_data = {
            "email": long_string,
            "password": long_string
        }
        
        response = await async_client.post("/api/auth/client-login", json=login_data)
        
        # Should handle gracefully
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    async def test_unicode_credentials(self, async_client):
        """Test authentication with unicode characters"""
        login_data = {
            "email": "用户@example.com",
            "password": "密码123"
        }
        
        response = await async_client.post("/api/auth/client-login", json=login_data)
        
        # Should return unauthorized, not cause an error
        assert response.status_code == status.HTTP_401_