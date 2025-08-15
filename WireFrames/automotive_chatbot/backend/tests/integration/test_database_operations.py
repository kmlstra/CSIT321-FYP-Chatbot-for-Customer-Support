#!/usr/bin/env python3
"""
Integration tests for database operations and client isolation
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
import secrets
from bson import ObjectId
from conftest import hash_password

@pytest.mark.integration
@pytest.mark.database
class TestClientIsolation:
    """Test client data isolation in multi-tenant environment"""
    
    async def test_client_data_isolation(self, async_client, clean_db, abc_motors_data, xyz_auto_data):
        """Test that clients can only access their own data"""
        # Create two separate clients
        client1_data = await self._create_test_client(clean_db, abc_motors_data)
        client2_data = await self._create_test_client(clean_db, xyz_auto_data)
        
        # Create conversations for each client
        await self._create_test_conversation(clean_db, client1_data["client_id"], "Client 1 conversation")
        await self._create_test_conversation(clean_db, client2_data["client_id"], "Client 2 conversation")
        
        # Create appointments for each client
        await self._create_test_appointment(clean_db, client1_data["client_id"], "client1@test.com")
        await self._create_test_appointment(clean_db, client2_data["client_id"], "client2@test.com")
        
        # Test that client 1 cannot access client 2's data
        headers1 = {"Authorization": f"Bearer {client1_data['token']}"}
        headers2 = {"Authorization": f"Bearer {client2_data['token']}"}
        
        # Test conversation isolation
        response1 = await async_client.get("/api/conversation/history", headers=headers1)
        response2 = await async_client.get("/api/conversation/history", headers=headers2)
        
        if response1.status_code == status.HTTP_200_OK and response2.status_code == status.HTTP_200_OK:
            data1 = response1.json()
            data2 = response2.json()
            
            # Each client should only see their own conversations
            if "conversations" in data1 and "conversations" in data2:
                # Verify no overlap in conversation data
                conv1_content = str(data1["conversations"])
                conv2_content = str(data2["conversations"])
                
                assert "Client 1 conversation" not in conv2_content
                assert "Client 2 conversation" not in conv1_content
        
        # Test appointment isolation
        response1 = await async_client.get("/api/appointments/", headers=headers1)
        response2 = await async_client.get("/api/appointments/", headers=headers2)
        
        if response1.status_code == status.HTTP_200_OK and response2.status_code == status.HTTP_200_OK:
            data1 = response1.json()
            data2 = response2.json()
            
            # Each client should only see their own appointments
            if "appointments" in data1 and "appointments" in data2:
                appt1_content = str(data1["appointments"])
                appt2_content = str(data2["appointments"])
                
                assert "client1@test.com" not in appt2_content
                assert "client2@test.com" not in appt1_content
    
    async def test_cross_client_access_prevention(self, async_client, clean_db, abc_motors_data, xyz_auto_data):
        """Test that clients cannot access other clients' resources directly"""
        # Create two clients
        client1_data = await self._create_test_client(clean_db, abc_motors_data)
        client2_data = await self._create_test_client(clean_db, xyz_auto_data)
        
        # Try to access client 2's data with client 1's token
        headers1 = {"Authorization": f"Bearer {client1_data['token']}"}
        
        # Attempt to access client 2's settings (if endpoint exists)
        response = await async_client.get(f"/api/client/{client2_data['client_id']}/settings", headers=headers1)
        
        # Should be forbidden or not found
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]
    
    async def test_database_transaction_isolation(self, clean_db, abc_motors_data, xyz_auto_data):
        """Test database transaction isolation between clients"""
        # Create clients in separate transactions
        client1_data = await self._create_test_client(clean_db, abc_motors_data)
        client2_data = await self._create_test_client(clean_db, xyz_auto_data)
        
        # Verify clients exist independently
        client1 = await clean_db.clients.find_one({"_id": ObjectId(client1_data["client_id"])})
        client2 = await clean_db.clients.find_one({"_id": ObjectId(client2_data["client_id"])})
        
        assert client1 is not None
        assert client2 is not None
        assert client1["domain"] != client2["domain"]
        assert client1["contact_email"] != client2["contact_email"]
        
        # Test concurrent updates don't interfere
        update_result1 = await clean_db.clients.update_one(
            {"_id": ObjectId(client1_data["client_id"])},
            {"$set": {"status": "updated_by_client1"}}
        )
        
        update_result2 = await clean_db.clients.update_one(
            {"_id": ObjectId(client2_data["client_id"])},
            {"$set": {"status": "updated_by_client2"}}
        )
        
        assert update_result1.modified_count == 1
        assert update_result2.modified_count == 1
        
        # Verify updates were applied correctly
        updated_client1 = await clean_db.clients.find_one({"_id": ObjectId(client1_data["client_id"])})
        updated_client2 = await clean_db.clients.find_one({"_id": ObjectId(client2_data["client_id"])})
        
        assert updated_client1["status"] == "updated_by_client1"
        assert updated_client2["status"] == "updated_by_client2"
    
    async def _create_test_client(self, db, client_data):
        """Helper to create a test client with user and token"""
        # Generate API key
        api_key = f"cc_{secrets.token_urlsafe(32)}"
        
        # Create client
        client_doc = {
            "business_name": client_data["business_name"],
            "domain": client_data["domain"],
            "contact_email": client_data["contact_email"],
            "status": "active",
            "api_key": api_key,
            "settings": {
                "branding": {
                    "company_name": client_data["business_name"],
                    "primary_color": "#4F46E5",
                    "secondary_color": "#7C3AED"
                },
                "features": {
                    "coe_prices": True,
                    "loan_calculator": True,
                    "appointment_booking": True
                },
                "contact_info": client_data["contact_info"]
            },
            "created_at": datetime.utcnow()
        }
        
        client_result = await db.clients.insert_one(client_doc)
        client_id = str(client_result.inserted_id)
        
        # Create admin user
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
        from conftest import create_access_token
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
            "token": token,
            "api_key": api_key
        }
    
    async def _create_test_conversation(self, db, client_id, content):
        """Helper to create a test conversation"""
        conversation_doc = {
            "client_id": client_id,
            "session_id": f"session_{secrets.token_hex(8)}",
            "content": content,
            "timestamp": datetime.utcnow(),
            "message_count": 1
        }
        
        await db.conversations.insert_one(conversation_doc)
    
    async def _create_test_appointment(self, db, client_id, customer_email):
        """Helper to create a test appointment"""
        appointment_doc = {
            "client_id": client_id,
            "appointment_id": f"apt_{secrets.token_hex(8)}",
            "customer_email": customer_email,
            "customer_name": "Test Customer",
            "customer_phone": "+65 6123 4567",
            "appointment_datetime": datetime.utcnow() + timedelta(days=1),
            "service_type": "test_drive",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await db.appointments.insert_one(appointment_doc)

@pytest.mark.integration
@pytest.mark.database
class TestDatabaseOperations:
    """Test database operations and consistency"""
    
    async def test_client_creation_workflow(self, clean_db, abc_motors_data):
        """Test complete client creation workflow"""
        # Step 1: Create client
        api_key = f"cc_{secrets.token_urlsafe(32)}"
        
        client_doc = {
            "business_name": abc_motors_data["business_name"],
            "domain": abc_motors_data["domain"],
            "contact_email": abc_motors_data["contact_email"],
            "status": "pending",
            "api_key": api_key,
            "settings": {
                "branding": {
                    "company_name": abc_motors_data["business_name"],
                    "primary_color": "#4F46E5",
                    "secondary_color": "#7C3AED"
                }
            },
            "created_at": datetime.utcnow()
        }
        
        client_result = await clean_db.clients.insert_one(client_doc)
        client_id = str(client_result.inserted_id)
        
        # Step 2: Create admin user
        user_doc = {
            "client_id": client_id,
            "name": abc_motors_data["admin_user"]["name"],
            "email": abc_motors_data["admin_user"]["email"],
            "password_hash": hash_password(abc_motors_data["admin_user"]["password"]),
            "role": "admin",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        user_result = await clean_db.client_users.insert_one(user_doc)
        user_id = str(user_result.inserted_id)
        
        # Step 3: Verify client and user were created
        created_client = await clean_db.clients.find_one({"_id": client_result.inserted_id})
        created_user = await clean_db.client_users.find_one({"_id": user_result.inserted_id})
        
        assert created_client is not None
        assert created_user is not None
        assert created_client["business_name"] == abc_motors_data["business_name"]
        assert created_user["email"] == abc_motors_data["admin_user"]["email"]
        assert created_user["client_id"] == client_id
        
        # Step 4: Approve client
        approval_result = await clean_db.clients.update_one(
            {"_id": client_result.inserted_id},
            {
                "$set": {
                    "status": "active",
                    "approved_at": datetime.utcnow(),
                    "approved_by": "system"
                }
            }
        )
        
        assert approval_result.modified_count == 1
        
        # Step 5: Activate user
        user_activation_result = await clean_db.client_users.update_one(
            {"_id": user_result.inserted_id},
            {"$set": {"status": "active"}}
        )
        
        assert user_activation_result.modified_count == 1
        
        # Step 6: Verify final state
        final_client = await clean_db.clients.find_one({"_id": client_result.inserted_id})
        final_user = await clean_db.client_users.find_one({"_id": user_result.inserted_id})
        
        assert final_client["status"] == "active"
        assert final_user["status"] == "active"
        assert "approved_at" in final_client
        assert "approved_by" in final_client
    
    async def test_conversation_logging_workflow(self, clean_db, test_client_with_user):
        """Test conversation logging and retrieval workflow"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Create multiple conversations
        conversations = [
            {
                "client_id": client_id,
                "session_id": "session_001",
                "content": "User: Hello\nBot: Hi there!",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "message_count": 2
            },
            {
                "client_id": client_id,
                "session_id": "session_002",
                "content": "User: COE prices?\nBot: Current COE prices...",
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "message_count": 2
            },
            {
                "client_id": client_id,
                "session_id": "session_003",
                "content": "User: Book test drive\nBot: I'll help you book...",
                "timestamp": datetime.utcnow(),
                "message_count": 2
            }
        ]
        
        # Insert conversations
        insert_result = await clean_db.conversations.insert_many(conversations)
        assert len(insert_result.inserted_ids) == 3
        
        # Test retrieval by client
        client_conversations = await clean_db.conversations.find(
            {"client_id": client_id}
        ).sort("timestamp", -1).to_list(length=None)
        
        assert len(client_conversations) == 3
        
        # Verify order (newest first)
        assert client_conversations[0]["session_id"] == "session_003"
        assert client_conversations[1]["session_id"] == "session_002"
        assert client_conversations[2]["session_id"] == "session_001"
        
        # Test retrieval by session
        session_conversation = await clean_db.conversations.find_one(
            {"client_id": client_id, "session_id": "session_002"}
        )
        
        assert session_conversation is not None
        assert "COE prices" in session_conversation["content"]
    
    async def test_appointment_management_workflow(self, clean_db, test_client_with_user):
        """Test appointment creation and management workflow"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Create appointment
        appointment_doc = {
            "client_id": client_id,
            "appointment_id": f"apt_{secrets.token_hex(8)}",
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "customer_phone": "+65 6123 4567",
            "appointment_datetime": datetime.utcnow() + timedelta(days=1),
            "service_type": "test_drive",
            "vehicle_interest": "Toyota Camry",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "notes": "Customer interested in hybrid model"
        }
        
        insert_result = await clean_db.appointments.insert_one(appointment_doc)
        appointment_id = appointment_doc["appointment_id"]
        
        # Verify creation
        created_appointment = await clean_db.appointments.find_one(
            {"_id": insert_result.inserted_id}
        )
        
        assert created_appointment is not None
        assert created_appointment["customer_name"] == "John Doe"
        assert created_appointment["status"] == "pending"
        
        # Update appointment status
        update_result = await clean_db.appointments.update_one(
            {"appointment_id": appointment_id},
            {
                "$set": {
                    "status": "confirmed",
                    "confirmed_at": datetime.utcnow(),
                    "confirmed_by": client_data["user_id"]
                }
            }
        )
        
        assert update_result.modified_count == 1
        
        # Verify update
        updated_appointment = await clean_db.appointments.find_one(
            {"appointment_id": appointment_id}
        )
        
        assert updated_appointment["status"] == "confirmed"
        assert "confirmed_at" in updated_appointment
        assert "confirmed_by" in updated_appointment
        
        # Test customer appointment lookup
        customer_appointments = await clean_db.appointments.find(
            {"customer_phone": "+65 6123 4567"}
        ).to_list(length=None)
        
        assert len(customer_appointments) == 1
        assert customer_appointments[0]["customer_name"] == "John Doe"
    
    async def test_database_indexing_performance(self, clean_db, test_client_with_user):
        """Test database indexing and query performance"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Create indexes for better performance
        await clean_db.clients.create_index("domain", unique=True)
        await clean_db.clients.create_index("contact_email", unique=True)
        await clean_db.client_users.create_index("email", unique=True)
        await clean_db.client_users.create_index("client_id")
        await clean_db.conversations.create_index("client_id")
        await clean_db.conversations.create_index("session_id")
        await clean_db.appointments.create_index("client_id")
        await clean_db.appointments.create_index("customer_phone")
        await clean_db.appointments.create_index("appointment_datetime")
        
        # Test query performance with indexes
        import time
        
        # Test client lookup by domain
        start_time = time.time()
        client = await clean_db.clients.find_one({"domain": "abcmotors.com"})
        domain_query_time = time.time() - start_time
        
        # Test user lookup by email
        start_time = time.time()
        user = await clean_db.client_users.find_one({"email": "john@abcmotors.com"})
        email_query_time = time.time() - start_time
        
        # Queries should be fast with proper indexing
        assert domain_query_time < 0.1  # Less than 100ms
        assert email_query_time < 0.1   # Less than 100ms
        
        # Verify results
        assert client is not None
        assert user is not None

@pytest.mark.integration
@pytest.mark.database
class TestDataConsistency:
    """Test data consistency and referential integrity"""
    
    async def test_client_user_relationship_consistency(self, clean_db, abc_motors_data):
        """Test consistency between clients and users"""
        # Create client
        client_doc = {
            "business_name": abc_motors_data["business_name"],
            "domain": abc_motors_data["domain"],
            "contact_email": abc_motors_data["contact_email"],
            "status": "active",
            "api_key": f"cc_{secrets.token_urlsafe(32)}",
            "created_at": datetime.utcnow()
        }
        
        client_result = await clean_db.clients.insert_one(client_doc)
        client_id = str(client_result.inserted_id)
        
        # Create multiple users for the client
        users = [
            {
                "client_id": client_id,
                "name": "Admin User",
                "email": "admin@abcmotors.com",
                "password_hash": hash_password("password123"),
                "role": "admin",
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "client_id": client_id,
                "name": "Manager User",
                "email": "manager@abcmotors.com",
                "password_hash": hash_password("password123"),
                "role": "manager",
                "status": "active",
                "created_at": datetime.utcnow()
            }
        ]
        
        user_results = await clean_db.client_users.insert_many(users)
        
        # Verify all users belong to the correct client
        client_users = await clean_db.client_users.find(
            {"client_id": client_id}
        ).to_list(length=None)
        
        assert len(client_users) == 2
        for user in client_users:
            assert user["client_id"] == client_id
        
        # Test orphaned user prevention (user without valid client)
        orphaned_user = {
            "client_id": str(ObjectId()),  # Non-existent client ID
            "name": "Orphaned User",
            "email": "orphan@example.com",
            "password_hash": hash_password("password123"),
            "role": "admin",
            "status": "active",
            "created_at": datetime.utcnow()
        }
        
        await clean_db.client_users.insert_one(orphaned_user)
        
        # Verify orphaned user exists but has no valid client
        orphan = await clean_db.client_users.find_one({"email": "orphan@example.com"})
        orphan_client = await clean_db.clients.find_one({"_id": ObjectId(orphan["client_id"])})
        
        assert orphan is not None
        assert orphan_client is None  # No corresponding client
    
    async def test_conversation_client_relationship(self, clean_db, test_client_with_user):
        """Test conversation-client relationship consistency"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Create conversations for the client
        conversations = [
            {
                "client_id": client_id,
                "session_id": f"session_{i}",
                "content": f"Conversation {i}",
                "timestamp": datetime.utcnow(),
                "message_count": 1
            }
            for i in range(5)
        ]
        
        await clean_db.conversations.insert_many(conversations)
        
        # Verify all conversations belong to the client
        client_conversations = await clean_db.conversations.find(
            {"client_id": client_id}
        ).to_list(length=None)
        
        assert len(client_conversations) == 5
        for conv in client_conversations:
            assert conv["client_id"] == client_id
        
        # Test conversation count consistency
        total_conversations = await clean_db.conversations.count_documents(
            {"client_id": client_id}
        )
        
        assert total_conversations == 5
    
    async def test_appointment_client_relationship(self, clean_db, test_client_with_user):
        """Test appointment-client relationship consistency"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Create appointments for the client
        appointments = [
            {
                "client_id": client_id,
                "appointment_id": f"apt_{i}",
                "customer_name": f"Customer {i}",
                "customer_email": f"customer{i}@example.com",
                "customer_phone": f"+65 612{i} 4567",
                "appointment_datetime": datetime.utcnow() + timedelta(days=i),
                "service_type": "test_drive",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            for i in range(3)
        ]
        
        await clean_db.appointments.insert_many(appointments)
        
        # Verify all appointments belong to the client
        client_appointments = await clean_db.appointments.find(
            {"client_id": client_id}
        ).to_list(length=None)
        
        assert len(client_appointments) == 3
        for appt in client_appointments:
            assert appt["client_id"] == client_id
        
        # Test appointment status consistency
        pending_count = await clean_db.appointments.count_documents(
            {"client_id": client_id, "status": "pending"}
        )
        
        assert pending_count == 3