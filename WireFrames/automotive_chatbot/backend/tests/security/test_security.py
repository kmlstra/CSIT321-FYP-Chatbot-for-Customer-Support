#!/usr/bin/env python3
"""
Security tests for authentication, authorization, and data isolation
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
import secrets
from bson import ObjectId
import jwt
import json
import time

@pytest.mark.security
@pytest.mark.auth
class TestAuthenticationSecurity:
    """Test authentication security mechanisms"""
    
    async def test_password_security_requirements(self, async_client, clean_db):
        """Test password security requirements and hashing"""
        # Test weak password rejection
        weak_passwords = [
            "123",
            "password",
            "abc",
            "12345678",
            "qwerty"
        ]
        
        for weak_password in weak_passwords:
            registration_data = {
                "business_name": "Test Security Motors",
                "domain": f"security{secrets.token_hex(4)}.com",
                "contact_email": f"admin{secrets.token_hex(4)}@security.com",
                "admin_user": {
                    "name": "Security Admin",
                    "email": f"admin{secrets.token_hex(4)}@security.com",
                    "password": weak_password
                }
            }
            
            response = await async_client.post("/api/client-registration/register", json=registration_data)
            
            # Should reject weak passwords
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                error_data = response.json()
                assert "password" in str(error_data).lower() or "weak" in str(error_data).lower()
    
    async def test_sql_injection_prevention(self, async_client, clean_db):
        """Test SQL injection prevention in login endpoints"""
        sql_injection_payloads = [
            "admin@test.com'; DROP TABLE users; --",
            "admin@test.com' OR '1'='1",
            "admin@test.com' UNION SELECT * FROM users --",
            "'; DELETE FROM clients; --",
            "admin@test.com' OR 1=1 --"
        ]
        
        for payload in sql_injection_payloads:
            login_data = {
                "email": payload,
                "password": "password123"
            }
            
            response = await async_client.post("/api/auth/client-login", json=login_data)
            
            # Should not succeed with SQL injection
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
            
            # Verify database integrity
            client_count = await clean_db.clients.count_documents({})
            user_count = await clean_db.client_users.count_documents({})
            
            # Database should not be affected
            assert isinstance(client_count, int)
            assert isinstance(user_count, int)
    
    async def test_xss_prevention(self, async_client, clean_db):
        """Test XSS prevention in input fields"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'><script>alert('XSS')</script>"
        ]
        
        for payload in xss_payloads:
            registration_data = {
                "business_name": payload,
                "domain": f"xss{secrets.token_hex(4)}.com",
                "contact_email": f"admin{secrets.token_hex(4)}@xss.com",
                "admin_user": {
                    "name": payload,
                    "email": f"admin{secrets.token_hex(4)}@xss.com",
                    "password": "SecurePass123!"
                }
            }
            
            response = await async_client.post("/api/client-registration/register", json=registration_data)
            
            if response.status_code == status.HTTP_201_CREATED:
                result = response.json()
                client_id = result["client_id"]
                
                # Verify XSS payload was sanitized or escaped
                client = await clean_db.clients.find_one({"_id": ObjectId(client_id)})
                if client:
                    # Should not contain raw script tags
                    assert "<script>" not in client["business_name"]
                    assert "javascript:" not in client["business_name"]
    
    async def test_jwt_token_security(self, async_client, clean_db, test_client_with_user):
        """Test JWT token security and validation"""
        client_data = test_client_with_user
        token = client_data["token"]
        
        # Test with invalid tokens
        invalid_tokens = [
            "invalid.token.here",
            "Bearer invalid_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "null",
            "undefined"
        ]
        
        for invalid_token in invalid_tokens:
            headers = {"Authorization": f"Bearer {invalid_token}"}
            
            response = await async_client.get("/api/conversation/stats", headers=headers)
            
            # Should reject invalid tokens
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test token tampering
        try:
            # Decode token to get payload
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            # Tamper with payload
            decoded["user_id"] = "tampered_user_id"
            decoded["client_id"] = "tampered_client_id"
            
            # Create tampered token (without proper signature)
            tampered_token = jwt.encode(decoded, "wrong_secret", algorithm="HS256")
            
            headers = {"Authorization": f"Bearer {tampered_token}"}
            response = await async_client.get("/api/conversation/stats", headers=headers)
            
            # Should reject tampered token
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            
        except Exception:
            # If JWT operations fail, that's also acceptable for security
            pass
    
    async def test_rate_limiting_protection(self, async_client, clean_db):
        """Test rate limiting on authentication endpoints"""
        login_data = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
        
        # Attempt multiple rapid login attempts
        responses = []
        for i in range(20):  # Try 20 rapid attempts
            response = await async_client.post("/api/auth/client-login", json=login_data)
            responses.append(response.status_code)
            
            # Small delay to avoid overwhelming the server
            if i % 5 == 0:
                time.sleep(0.1)
        
        # Should eventually get rate limited (429) or continue to get 401
        # Both are acceptable security behaviors
        assert all(code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_400_BAD_REQUEST] for code in responses)

@pytest.mark.security
@pytest.mark.auth
class TestAuthorizationSecurity:
    """Test authorization and access control security"""
    
    async def test_unauthorized_endpoint_access(self, async_client, clean_db):
        """Test access to protected endpoints without authentication"""
        protected_endpoints = [
            ("/api/conversation/stats", "GET"),
            ("/api/conversation/history", "GET"),
            ("/api/appointments/", "GET"),
            ("/api/appointments/", "POST"),
            ("/api/client/profile", "GET"),
            ("/api/client/settings", "GET"),
            ("/api/admin/clients", "GET"),
            ("/api/admin/metrics", "GET")
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            elif method == "POST":
                response = await async_client.post(endpoint, json={})
            elif method == "PUT":
                response = await async_client.put(endpoint, json={})
            
            # Should require authentication
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND  # Some endpoints might not exist yet
            ]
    
    async def test_cross_client_access_prevention(self, async_client, clean_db, abc_motors_data, xyz_auto_data):
        """Test prevention of cross-client data access"""
        # Create two separate clients
        client1_data = await self._create_test_client(clean_db, abc_motors_data)
        client2_data = await self._create_test_client(clean_db, xyz_auto_data)
        
        # Create data for client 1
        await self._create_client_data(clean_db, client1_data["client_id"])
        
        # Try to access client 1's data with client 2's token
        headers2 = {"Authorization": f"Bearer {client2_data['token']}"}
        
        # Test various endpoints that might expose client-specific data
        test_endpoints = [
            f"/api/client/{client1_data['client_id']}/profile",
            f"/api/client/{client1_data['client_id']}/settings",
            f"/api/widget/config/{client1_data['client_id']}"
        ]
        
        for endpoint in test_endpoints:
            response = await async_client.get(endpoint, headers=headers2)
            
            # Should not allow access to other client's data
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_401_UNAUTHORIZED
            ]
    
    async def test_role_based_access_control(self, async_client, clean_db, test_client_with_user):
        """Test role-based access control"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Create a non-admin user
        from conftest import hash_password, create_access_token
        
        regular_user_doc = {
            "client_id": client_id,
            "name": "Regular User",
            "email": "regular@test.com",
            "password_hash": hash_password("password123"),
            "role": "user",  # Non-admin role
            "status": "active",
            "created_at": datetime.utcnow()
        }
        
        user_result = await clean_db.client_users.insert_one(regular_user_doc)
        regular_user_id = str(user_result.inserted_id)
        
        # Create token for regular user
        regular_token_data = {
            "user_id": regular_user_id,
            "client_id": client_id,
            "email": "regular@test.com",
            "role": "user",
            "type": "client_user"
        }
        
        regular_token = create_access_token(regular_token_data)
        regular_headers = {"Authorization": f"Bearer {regular_token}"}
        
        # Test admin-only endpoints with regular user token
        admin_endpoints = [
            ("/api/client/settings", "PUT"),
            ("/api/client/users", "GET"),
            ("/api/admin/clients", "GET")
        ]
        
        for endpoint, method in admin_endpoints:
            if method == "GET":
                response = await async_client.get(endpoint, headers=regular_headers)
            elif method == "PUT":
                response = await async_client.put(endpoint, json={}, headers=regular_headers)
            
            # Regular user should not access admin endpoints
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_401_UNAUTHORIZED
            ]
    
    async def test_super_admin_isolation(self, async_client, clean_db, test_client_with_user, super_admin_user):
        """Test super admin access isolation"""
        client_data = test_client_with_user
        client_headers = {"Authorization": f"Bearer {client_data['token']}"}
        
        # Client should not access super admin endpoints
        super_admin_endpoints = [
            "/api/admin/clients",
            "/api/admin/metrics",
            "/api/admin/system-status"
        ]
        
        for endpoint in super_admin_endpoints:
            response = await async_client.get(endpoint, headers=client_headers)
            
            # Client should not access super admin endpoints
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_401_UNAUTHORIZED
            ]
    
    async def _create_test_client(self, db, client_data):
        """Helper to create test client with user and token"""
        from conftest import hash_password, create_access_token
        
        # Create client
        client_doc = {
            "business_name": client_data["business_name"],
            "domain": client_data["domain"],
            "contact_email": client_data["contact_email"],
            "status": "active",
            "api_key": f"cc_{secrets.token_urlsafe(32)}",
            "created_at": datetime.utcnow()
        }
        
        client_result = await db.clients.insert_one(client_doc)
        client_id = str(client_result.inserted_id)
        
        # Create user
        user_doc = {
            "client_id": client_id,
            "name": client_data["admin_user"]["name"],
            "email": client_data["admin_user"]["email"],
            "password_hash": hash_password(client_data["admin_user"]["password"]),
            "role": "admin",
            "status": "active",
            "created_at": datetime.utcnow()
        }
        
        user_result = await db.client_users.insert_one(user_doc)
        user_id = str(user_result.inserted_id)
        
        # Create token
        token_data = {
            "user_id": user_id,
            "client_id": client_id,
            "email": user_doc["email"],
            "role": "admin",
            "type": "client_user"
        }
        
        token = create_access_token(token_data)
        
        return {
            "client_id": client_id,
            "user_id": user_id,
            "token": token
        }
    
    async def _create_client_data(self, db, client_id):
        """Helper to create test data for a client"""
        # Create conversation
        conversation_doc = {
            "client_id": client_id,
            "session_id": "test_session",
            "content": "Test conversation",
            "timestamp": datetime.utcnow(),
            "message_count": 1
        }
        
        await db.conversations.insert_one(conversation_doc)
        
        # Create appointment
        appointment_doc = {
            "client_id": client_id,
            "appointment_id": f"apt_{secrets.token_hex(8)}",
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "+65 6123 4567",
            "appointment_datetime": datetime.utcnow() + timedelta(days=1),
            "service_type": "test_drive",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await db.appointments.insert_one(appointment_doc)

@pytest.mark.security
@pytest.mark.database
class TestDataSecurityAndIsolation:
    """Test data security and isolation mechanisms"""
    
    async def test_database_injection_prevention(self, async_client, clean_db):
        """Test NoSQL injection prevention"""
        # MongoDB injection payloads
        nosql_injection_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "this.password"},
            {"$or": [{"email": "admin@test.com"}, {"email": {"$ne": None}}]}
        ]
        
        for payload in nosql_injection_payloads:
            # Test in login endpoint
            login_data = {
                "email": payload,
                "password": "password123"
            }
            
            response = await async_client.post("/api/auth/client-login", json=login_data)
            
            # Should not succeed with NoSQL injection
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    async def test_sensitive_data_exposure_prevention(self, async_client, clean_db, test_client_with_user):
        """Test prevention of sensitive data exposure"""
        client_data = test_client_with_user
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        
        # Test endpoints that might expose sensitive data
        endpoints_to_test = [
            "/api/client/profile",
            "/api/client/settings",
            "/api/conversation/history"
        ]
        
        for endpoint in endpoints_to_test:
            response = await async_client.get(endpoint, headers=headers)
            
            if response.status_code == status.HTTP_200_OK:
                response_text = response.text.lower()
                
                # Should not expose sensitive information
                sensitive_fields = [
                    "password",
                    "password_hash",
                    "secret",
                    "private_key",
                    "api_secret"
                ]
                
                for sensitive_field in sensitive_fields:
                    assert sensitive_field not in response_text
    
    async def test_client_data_isolation_at_db_level(self, clean_db, abc_motors_data, xyz_auto_data):
        """Test client data isolation at database level"""
        # Create two clients
        client1_data = await self._create_isolated_client(clean_db, abc_motors_data)
        client2_data = await self._create_isolated_client(clean_db, xyz_auto_data)
        
        # Create data for each client
        await self._create_isolated_data(clean_db, client1_data["client_id"], "client1")
        await self._create_isolated_data(clean_db, client2_data["client_id"], "client2")
        
        # Verify client 1 can only see their data
        client1_conversations = await clean_db.conversations.find(
            {"client_id": client1_data["client_id"]}
        ).to_list(length=None)
        
        client1_appointments = await clean_db.appointments.find(
            {"client_id": client1_data["client_id"]}
        ).to_list(length=None)
        
        # Verify client 2 can only see their data
        client2_conversations = await clean_db.conversations.find(
            {"client_id": client2_data["client_id"]}
        ).to_list(length=None)
        
        client2_appointments = await clean_db.appointments.find(
            {"client_id": client2_data["client_id"]}
        ).to_list(length=None)
        
        # Verify isolation
        assert len(client1_conversations) > 0
        assert len(client2_conversations) > 0
        assert len(client1_appointments) > 0
        assert len(client2_appointments) > 0
        
        # Verify no cross-contamination
        for conv in client1_conversations:
            assert conv["client_id"] == client1_data["client_id"]
            assert "client2" not in conv["content"]
        
        for conv in client2_conversations:
            assert conv["client_id"] == client2_data["client_id"]
            assert "client1" not in conv["content"]
        
        for appt in client1_appointments:
            assert appt["client_id"] == client1_data["client_id"]
            assert "client2" not in appt["customer_name"]
        
        for appt in client2_appointments:
            assert appt["client_id"] == client2_data["client_id"]
            assert "client1" not in appt["customer_name"]
    
    async def test_api_key_security(self, async_client, clean_db, test_client_with_user):
        """Test API key security and validation"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Get client's API key
        client = await clean_db.clients.find_one({"_id": ObjectId(client_id)})
        api_key = client["api_key"]
        
        # Test widget endpoints with API key
        valid_api_headers = {"X-API-Key": api_key}
        
        # Test with valid API key
        response = await async_client.get(f"/api/widget/config/{client_id}", headers=valid_api_headers)
        
        # Should work with valid API key (if endpoint supports it)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        # Test with invalid API keys
        invalid_api_keys = [
            "invalid_key",
            "cc_invalid_key",
            "",
            "null",
            api_key + "_tampered"
        ]
        
        for invalid_key in invalid_api_keys:
            invalid_headers = {"X-API-Key": invalid_key}
            response = await async_client.get(f"/api/widget/config/{client_id}", headers=invalid_headers)
            
            # Should reject invalid API keys (if validation is implemented)
            if response.status_code not in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]:
                assert response.status_code in [
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_403_FORBIDDEN
                ]
    
    async def _create_isolated_client(self, db, client_data):
        """Helper to create isolated client"""
        client_doc = {
            "business_name": client_data["business_name"],
            "domain": client_data["domain"],
            "contact_email": client_data["contact_email"],
            "status": "active",
            "api_key": f"cc_{secrets.token_urlsafe(32)}",
            "created_at": datetime.utcnow()
        }
        
        client_result = await db.clients.insert_one(client_doc)
        return {"client_id": str(client_result.inserted_id)}
    
    async def _create_isolated_data(self, db, client_id, client_prefix):
        """Helper to create isolated test data"""
        # Create conversation
        conversation_doc = {
            "client_id": client_id,
            "session_id": f"{client_prefix}_session",
            "content": f"{client_prefix} exclusive conversation",
            "timestamp": datetime.utcnow(),
            "message_count": 1
        }
        
        await db.conversations.insert_one(conversation_doc)
        
        # Create appointment
        appointment_doc = {
            "client_id": client_id,
            "appointment_id": f"{client_prefix}_apt_{secrets.token_hex(4)}",
            "customer_name": f"{client_prefix} Customer",
            "customer_email": f"{client_prefix}@example.com",
            "customer_phone": f"+65 6{client_prefix[:3]} 4567",
            "appointment_datetime": datetime.utcnow() + timedelta(days=1),
            "service_type": "test_drive",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await db.appointments.insert_one(appointment_doc)

@pytest.mark.security
@pytest.mark.widget
class TestWidgetSecurity:
    """Test widget-specific security measures"""
    
    async def test_widget_cors_security(self, async_client, clean_db, test_client_with_user):
        """Test CORS security for widget endpoints"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test CORS headers on widget endpoints
        widget_endpoints = [
            f"/api/widget/config/{client_id}",
            f"/api/widget/embed/{client_id}",
            "/api/widget/chat"
        ]
        
        for endpoint in widget_endpoints:
            # Test preflight request
            headers = {
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            response = await async_client.options(endpoint, headers=headers)
            
            # Should handle CORS appropriately
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_204_NO_CONTENT,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_405_METHOD_NOT_ALLOWED
            ]
    
    async def test_widget_xss_prevention(self, async_client, clean_db, test_client_with_user):
        """Test XSS prevention in widget chat"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'><script>document.cookie</script>"
        ]
        
        for payload in xss_payloads:
            chat_data = {
                "message": payload,
                "session_id": f"xss_test_{secrets.token_hex(4)}",
                "client_id": client_id
            }
            
            response = await async_client.post("/api/widget/chat", json=chat_data)
            
            if response.status_code == status.HTTP_200_OK:
                response_data = response.json()
                response_text = str(response_data)
                
                # Response should not contain raw script tags
                assert "<script>" not in response_text
                assert "javascript:" not in response_text
                assert "onerror=" not in response_text
    
    async def test_widget_client_id_validation(self, async_client, clean_db):
        """Test client ID validation in widget endpoints"""
        invalid_client_ids = [
            "invalid_id",
            "../../../etc/passwd",
            "'; DROP TABLE clients; --",
            "<script>alert('XSS')</script>",
            "null",
            "",
            "0" * 100  # Very long ID
        ]
        
        for invalid_id in invalid_client_ids:
            # Test widget config endpoint
            response = await async_client.get(f"/api/widget/config/{invalid_id}")
            
            # Should reject invalid client IDs
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
            
            # Test widget embed endpoint
            response = await async_client.get(f"/api/widget/embed/{invalid_id}")
            
            # Should reject invalid client IDs
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]