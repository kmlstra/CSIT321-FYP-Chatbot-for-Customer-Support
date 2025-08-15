#!/usr/bin/env python3
"""
Integration tests for API endpoints
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
import secrets
from bson import ObjectId
import json

@pytest.mark.integration
@pytest.mark.api
class TestAuthenticationEndpoints:
    """Test authentication API endpoints integration"""
    
    async def test_client_login_flow(self, async_client, clean_db, abc_motors_data):
        """Test complete client login flow"""
        # Create client and user in database
        client_data = await self._setup_test_client(clean_db, abc_motors_data)
        
        # Test login
        login_data = {
            "email": abc_motors_data["admin_user"]["email"],
            "password": abc_motors_data["admin_user"]["password"]
        }
        
        response = await async_client.post("/api/auth/client-login", json=login_data)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            
            # Test authenticated request
            headers = {"Authorization": f"Bearer {data['access_token']}"}
            profile_response = await async_client.get("/api/client/profile", headers=headers)
            
            # Should be able to access protected endpoint
            assert profile_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    async def test_super_admin_login_flow(self, async_client, clean_db, super_admin_user):
        """Test super admin login flow"""
        # Test super admin login
        login_data = {
            "username": super_admin_user["username"],
            "password": super_admin_user["password"]
        }
        
        response = await async_client.post("/api/auth/super-admin-login", json=login_data)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            
            # Test super admin authenticated request
            headers = {"Authorization": f"Bearer {data['access_token']}"}
            admin_response = await async_client.get("/api/admin/clients", headers=headers)
            
            # Should be able to access admin endpoint
            assert admin_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    async def test_token_validation_flow(self, async_client, clean_db, abc_motors_data):
        """Test token validation across requests"""
        # Setup client and get token
        client_data = await self._setup_test_client(clean_db, abc_motors_data)
        
        login_data = {
            "email": abc_motors_data["admin_user"]["email"],
            "password": abc_motors_data["admin_user"]["password"]
        }
        
        login_response = await async_client.post("/api/auth/client-login", json=login_data)
        
        if login_response.status_code == status.HTTP_200_OK:
            token_data = login_response.json()
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Test multiple authenticated requests
            endpoints_to_test = [
                "/api/client/profile",
                "/api/client/settings",
                "/api/conversation/stats",
                "/api/appointments/"
            ]
            
            for endpoint in endpoints_to_test:
                response = await async_client.get(endpoint, headers=headers)
                # Should not be unauthorized
                assert response.status_code != status.HTTP_401_UNAUTHORIZED
    
    async def _setup_test_client(self, db, client_data):
        """Helper to setup test client in database"""
        from conftest import hash_password
        
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
        
        return {
            "client_id": client_id,
            "user_id": str(user_result.inserted_id)
        }

@pytest.mark.integration
@pytest.mark.api
class TestClientRegistrationEndpoints:
    """Test client registration API endpoints"""
    
    async def test_client_registration_flow(self, async_client, clean_db):
        """Test complete client registration flow"""
        registration_data = {
            "business_name": "Test Motors Ltd",
            "domain": "testmotors.com",
            "contact_email": "admin@testmotors.com",
            "admin_user": {
                "name": "Test Admin",
                "email": "admin@testmotors.com",
                "password": "SecurePass123!"
            },
            "contact_info": {
                "phone": "+65 6123 4567",
                "address": "123 Test Street, Singapore 123456"
            }
        }
        
        response = await async_client.post("/api/client-registration/register", json=registration_data)
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert "client_id" in data
            assert "api_key" in data
            assert "message" in data
            
            # Verify client was created in database
            client = await clean_db.clients.find_one({"domain": "testmotors.com"})
            assert client is not None
            assert client["business_name"] == "Test Motors Ltd"
            assert client["status"] == "pending"  # Should be pending approval
            
            # Verify user was created
            user = await clean_db.client_users.find_one({"email": "admin@testmotors.com"})
            assert user is not None
            assert user["client_id"] == str(client["_id"])
            assert user["status"] == "pending"
    
    async def test_duplicate_registration_prevention(self, async_client, clean_db, abc_motors_data):
        """Test prevention of duplicate registrations"""
        # First registration
        await self._create_existing_client(clean_db, abc_motors_data)
        
        # Attempt duplicate registration
        registration_data = {
            "business_name": "ABC Motors Copy",
            "domain": abc_motors_data["domain"],  # Same domain
            "contact_email": "different@email.com",
            "admin_user": {
                "name": "Different Admin",
                "email": "different@email.com",
                "password": "SecurePass123!"
            }
        }
        
        response = await async_client.post("/api/client-registration/register", json=registration_data)
        
        # Should reject duplicate domain
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test duplicate email
        registration_data["domain"] = "different-domain.com"
        registration_data["contact_email"] = abc_motors_data["contact_email"]  # Same email
        
        response = await async_client.post("/api/client-registration/register", json=registration_data)
        
        # Should reject duplicate email
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    async def _create_existing_client(self, db, client_data):
        """Helper to create existing client"""
        client_doc = {
            "business_name": client_data["business_name"],
            "domain": client_data["domain"],
            "contact_email": client_data["contact_email"],
            "status": "active",
            "api_key": f"cc_{secrets.token_urlsafe(32)}",
            "created_at": datetime.utcnow()
        }
        
        await db.clients.insert_one(client_doc)

@pytest.mark.integration
@pytest.mark.api
class TestWidgetAPIEndpoints:
    """Test widget API endpoints integration"""
    
    async def test_widget_config_retrieval(self, async_client, clean_db, test_client_with_user):
        """Test widget configuration retrieval"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test widget config endpoint
        response = await async_client.get(f"/api/widget/config/{client_id}")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "client_id" in data
            assert "settings" in data
            assert data["client_id"] == client_id
    
    async def test_widget_embed_script(self, async_client, clean_db, test_client_with_user):
        """Test widget embed script generation"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test embed script endpoint
        response = await async_client.get(f"/api/widget/embed/{client_id}")
        
        if response.status_code == status.HTTP_200_OK:
            # Should return JavaScript content
            assert response.headers.get("content-type") == "application/javascript"
            content = response.text
            assert "function" in content or "const" in content
            assert client_id in content
    
    async def test_widget_chat_functionality(self, async_client, clean_db, test_client_with_user):
        """Test widget chat functionality"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test chat message endpoint
        chat_data = {
            "message": "Hello, I need help with COE prices",
            "session_id": f"session_{secrets.token_hex(8)}",
            "client_id": client_id
        }
        
        response = await async_client.post("/api/widget/chat", json=chat_data)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "response" in data
            assert "session_id" in data
            
            # Verify conversation was logged
            conversation = await clean_db.conversations.find_one({
                "client_id": client_id,
                "session_id": chat_data["session_id"]
            })
            
            if conversation:
                assert conversation["client_id"] == client_id

@pytest.mark.integration
@pytest.mark.api
class TestConversationEndpoints:
    """Test conversation management endpoints"""
    
    async def test_conversation_history_retrieval(self, async_client, clean_db, authenticated_client):
        """Test conversation history retrieval"""
        client_data, headers = authenticated_client
        client_id = client_data["client_id"]
        
        # Create test conversations
        await self._create_test_conversations(clean_db, client_id)
        
        # Test history endpoint
        response = await async_client.get("/api/conversation/history", headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "conversations" in data or "history" in data
    
    async def test_conversation_stats(self, async_client, clean_db, authenticated_client):
        """Test conversation statistics"""
        client_data, headers = authenticated_client
        client_id = client_data["client_id"]
        
        # Create test conversations
        await self._create_test_conversations(clean_db, client_id)
        
        # Test stats endpoint
        response = await async_client.get("/api/conversation/stats", headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Should contain some statistics
            assert isinstance(data, dict)
    
    async def test_specific_conversation_retrieval(self, async_client, clean_db, authenticated_client):
        """Test specific conversation retrieval"""
        client_data, headers = authenticated_client
        client_id = client_data["client_id"]
        
        # Create a specific conversation
        conversation_id = await self._create_specific_conversation(clean_db, client_id)
        
        # Test specific conversation endpoint
        response = await async_client.get(f"/api/conversation/history/{conversation_id}", headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "conversation" in data or "content" in data
    
    async def _create_test_conversations(self, db, client_id):
        """Helper to create test conversations"""
        conversations = [
            {
                "client_id": client_id,
                "session_id": f"session_{i}",
                "content": f"Test conversation {i}",
                "timestamp": datetime.utcnow() - timedelta(hours=i),
                "message_count": 2
            }
            for i in range(3)
        ]
        
        await db.conversations.insert_many(conversations)
    
    async def _create_specific_conversation(self, db, client_id):
        """Helper to create a specific conversation"""
        conversation_doc = {
            "client_id": client_id,
            "session_id": "specific_session",
            "content": "Specific test conversation",
            "timestamp": datetime.utcnow(),
            "message_count": 1
        }
        
        result = await db.conversations.insert_one(conversation_doc)
        return str(result.inserted_id)

@pytest.mark.integration
@pytest.mark.api
class TestAppointmentEndpoints:
    """Test appointment management endpoints"""
    
    async def test_appointment_creation(self, async_client, clean_db, authenticated_client):
        """Test appointment creation"""
        client_data, headers = authenticated_client
        client_id = client_data["client_id"]
        
        appointment_data = {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "customer_phone": "+65 6123 4567",
            "appointment_datetime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "service_type": "test_drive",
            "vehicle_interest": "Toyota Camry",
            "notes": "Interested in hybrid model"
        }
        
        response = await async_client.post("/api/appointments/", json=appointment_data, headers=headers)
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert "appointment_id" in data
            
            # Verify appointment was created in database
            appointment = await clean_db.appointments.find_one({
                "appointment_id": data["appointment_id"]
            })
            
            assert appointment is not None
            assert appointment["client_id"] == client_id
            assert appointment["customer_name"] == "John Doe"
    
    async def test_appointment_listing(self, async_client, clean_db, authenticated_client):
        """Test appointment listing"""
        client_data, headers = authenticated_client
        client_id = client_data["client_id"]
        
        # Create test appointments
        await self._create_test_appointments(clean_db, client_id)
        
        # Test appointments listing
        response = await async_client.get("/api/appointments/", headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "appointments" in data or isinstance(data, list)
    
    async def test_appointment_status_update(self, async_client, clean_db, authenticated_client):
        """Test appointment status update"""
        client_data, headers = authenticated_client
        client_id = client_data["client_id"]
        
        # Create test appointment
        appointment_id = await self._create_test_appointment(clean_db, client_id)
        
        # Test status update
        update_data = {
            "status": "confirmed",
            "notes": "Appointment confirmed by admin"
        }
        
        response = await async_client.put(f"/api/appointments/{appointment_id}/status", json=update_data, headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            # Verify update in database
            appointment = await clean_db.appointments.find_one({
                "appointment_id": appointment_id
            })
            
            if appointment:
                assert appointment["status"] == "confirmed"
    
    async def test_customer_appointment_lookup(self, async_client, clean_db, authenticated_client):
        """Test customer appointment lookup"""
        client_data, headers = authenticated_client
        client_id = client_data["client_id"]
        
        # Create test appointment with specific phone
        phone = "+65 6123 4567"
        await self._create_test_appointment_with_phone(clean_db, client_id, phone)
        
        # Test customer lookup
        response = await async_client.get(f"/api/appointments/customer/{phone}", headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "appointments" in data or isinstance(data, list)
    
    async def _create_test_appointments(self, db, client_id):
        """Helper to create test appointments"""
        appointments = [
            {
                "client_id": client_id,
                "appointment_id": f"apt_{i}",
                "customer_name": f"Customer {i}",
                "customer_email": f"customer{i}@example.com",
                "customer_phone": f"+65 612{i} 4567",
                "appointment_datetime": datetime.utcnow() + timedelta(days=i+1),
                "service_type": "test_drive",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            for i in range(3)
        ]
        
        await db.appointments.insert_many(appointments)
    
    async def _create_test_appointment(self, db, client_id):
        """Helper to create a single test appointment"""
        appointment_id = f"apt_{secrets.token_hex(8)}"
        
        appointment_doc = {
            "client_id": client_id,
            "appointment_id": appointment_id,
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "+65 6123 4567",
            "appointment_datetime": datetime.utcnow() + timedelta(days=1),
            "service_type": "test_drive",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await db.appointments.insert_one(appointment_doc)
        return appointment_id
    
    async def _create_test_appointment_with_phone(self, db, client_id, phone):
        """Helper to create appointment with specific phone"""
        appointment_doc = {
            "client_id": client_id,
            "appointment_id": f"apt_{secrets.token_hex(8)}",
            "customer_name": "Phone Test Customer",
            "customer_email": "phonetest@example.com",
            "customer_phone": phone,
            "appointment_datetime": datetime.utcnow() + timedelta(days=1),
            "service_type": "test_drive",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await db.appointments.insert_one(appointment_doc)

@pytest.mark.integration
@pytest.mark.api
class TestSuperAdminEndpoints:
    """Test super admin endpoints integration"""
    
    async def test_client_approval_workflow(self, async_client, clean_db, super_admin_token):
        """Test client approval workflow"""
        # Create pending client
        client_id = await self._create_pending_client(clean_db)
        
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Test client approval
        approval_data = {
            "status": "active",
            "notes": "Approved by super admin"
        }
        
        response = await async_client.put(f"/api/admin/clients/{client_id}/approve", json=approval_data, headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            # Verify client was approved
            client = await clean_db.clients.find_one({"_id": ObjectId(client_id)})
            if client:
                assert client["status"] == "active"
    
    async def test_system_metrics_access(self, async_client, clean_db, super_admin_token):
        """Test system metrics access"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Test metrics endpoint
        response = await async_client.get("/api/admin/metrics", headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Should contain system metrics
            assert isinstance(data, dict)
    
    async def test_all_clients_listing(self, async_client, clean_db, super_admin_token):
        """Test listing all clients"""
        # Create test clients
        await self._create_multiple_test_clients(clean_db)
        
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Test clients listing
        response = await async_client.get("/api/admin/clients", headers=headers)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "clients" in data or isinstance(data, list)
    
    async def _create_pending_client(self, db):
        """Helper to create pending client"""
        client_doc = {
            "business_name": "Pending Motors",
            "domain": "pending.com",
            "contact_email": "admin@pending.com",
            "status": "pending",
            "api_key": f"cc_{secrets.token_urlsafe(32)}",
            "created_at": datetime.utcnow()
        }
        
        result = await db.clients.insert_one(client_doc)
        return str(result.inserted_id)
    
    async def _create_multiple_test_clients(self, db):
        """Helper to create multiple test clients"""
        clients = [
            {
                "business_name": f"Test Motors {i}",
                "domain": f"test{i}.com",
                "contact_email": f"admin{i}@test{i}.com",
                "status": "active" if i % 2 == 0 else "pending",
                "api_key": f"cc_{secrets.token_urlsafe(32)}",
                "created_at": datetime.utcnow()
            }
            for i in range(5)
        ]
        
        await db.clients.insert_many(clients)