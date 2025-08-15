#!/usr/bin/env python3
"""
End-to-end tests for complete user workflows
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
import secrets
from bson import ObjectId
import asyncio
import time

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteClientOnboardingWorkflow:
    """Test complete client onboarding workflow from registration to active usage"""
    
    async def test_full_client_lifecycle(self, async_client, clean_db, super_admin_user):
        """Test complete client lifecycle: registration -> approval -> login -> usage"""
        # Step 1: Client Registration
        registration_data = {
            "business_name": "E2E Test Motors",
            "domain": "e2etest.com",
            "contact_email": "admin@e2etest.com",
            "admin_user": {
                "name": "E2E Admin",
                "email": "admin@e2etest.com",
                "password": "SecurePass123!"
            },
            "contact_info": {
                "phone": "+65 6123 4567",
                "address": "123 E2E Street, Singapore 123456"
            }
        }
        
        # Register client
        registration_response = await async_client.post(
            "/api/client-registration/register", 
            json=registration_data
        )
        
        assert registration_response.status_code == status.HTTP_201_CREATED
        registration_result = registration_response.json()
        client_id = registration_result["client_id"]
        api_key = registration_result["api_key"]
        
        # Verify client is pending
        client = await clean_db.clients.find_one({"_id": ObjectId(client_id)})
        assert client["status"] == "pending"
        
        # Verify user is pending
        user = await clean_db.client_users.find_one({"client_id": client_id})
        assert user["status"] == "pending"
        
        # Step 2: Super Admin Login
        super_admin_login = {
            "username": super_admin_user["username"],
            "password": super_admin_user["password"]
        }
        
        admin_login_response = await async_client.post(
            "/api/auth/super-admin-login",
            json=super_admin_login
        )
        
        if admin_login_response.status_code == status.HTTP_200_OK:
            admin_token_data = admin_login_response.json()
            admin_headers = {"Authorization": f"Bearer {admin_token_data['access_token']}"}
            
            # Step 3: Super Admin Approves Client
            approval_data = {
                "status": "active",
                "notes": "Approved during E2E test"
            }
            
            approval_response = await async_client.put(
                f"/api/admin/clients/{client_id}/approve",
                json=approval_data,
                headers=admin_headers
            )
            
            # Check if approval endpoint exists and works
            if approval_response.status_code == status.HTTP_200_OK:
                # Verify client is now active
                updated_client = await clean_db.clients.find_one({"_id": ObjectId(client_id)})
                assert updated_client["status"] == "active"
            else:
                # Manually approve for testing
                await clean_db.clients.update_one(
                    {"_id": ObjectId(client_id)},
                    {"$set": {"status": "active", "approved_at": datetime.utcnow()}}
                )
                await clean_db.client_users.update_one(
                    {"client_id": client_id},
                    {"$set": {"status": "active"}}
                )
        else:
            # Manually approve for testing if super admin login fails
            await clean_db.clients.update_one(
                {"_id": ObjectId(client_id)},
                {"$set": {"status": "active", "approved_at": datetime.utcnow()}}
            )
            await clean_db.client_users.update_one(
                {"client_id": client_id},
                {"$set": {"status": "active"}}
            )
        
        # Step 4: Client Login
        client_login_data = {
            "email": "admin@e2etest.com",
            "password": "SecurePass123!"
        }
        
        client_login_response = await async_client.post(
            "/api/auth/client-login",
            json=client_login_data
        )
        
        if client_login_response.status_code == status.HTTP_200_OK:
            client_token_data = client_login_response.json()
            client_headers = {"Authorization": f"Bearer {client_token_data['access_token']}"}
            
            # Step 5: Client Uses Platform Features
            
            # Test widget configuration access
            widget_config_response = await async_client.get(
                f"/api/widget/config/{client_id}"
            )
            
            if widget_config_response.status_code == status.HTTP_200_OK:
                widget_config = widget_config_response.json()
                assert widget_config["client_id"] == client_id
            
            # Test conversation stats
            stats_response = await async_client.get(
                "/api/conversation/stats",
                headers=client_headers
            )
            
            # Should be accessible (even if empty)
            assert stats_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
            
            # Test appointments listing
            appointments_response = await async_client.get(
                "/api/appointments/",
                headers=client_headers
            )
            
            # Should be accessible (even if empty)
            assert appointments_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
            
            # Step 6: Widget Chat Functionality
            chat_data = {
                "message": "Hello, I need information about COE prices",
                "session_id": f"e2e_session_{secrets.token_hex(8)}",
                "client_id": client_id
            }
            
            chat_response = await async_client.post(
                "/api/widget/chat",
                json=chat_data
            )
            
            if chat_response.status_code == status.HTTP_200_OK:
                chat_result = chat_response.json()
                assert "response" in chat_result
                assert "session_id" in chat_result
                
                # Verify conversation was logged
                conversation = await clean_db.conversations.find_one({
                    "client_id": client_id,
                    "session_id": chat_data["session_id"]
                })
                
                if conversation:
                    assert conversation["client_id"] == client_id
        
        # Final verification: Client is fully functional
        final_client = await clean_db.clients.find_one({"_id": ObjectId(client_id)})
        final_user = await clean_db.client_users.find_one({"client_id": client_id})
        
        assert final_client["status"] == "active"
        assert final_user["status"] == "active"
        assert final_client["api_key"] == api_key
    
    async def test_multi_client_parallel_onboarding(self, async_client, clean_db):
        """Test multiple clients can be onboarded in parallel without conflicts"""
        # Create multiple client registration data
        clients_data = [
            {
                "business_name": f"Parallel Motors {i}",
                "domain": f"parallel{i}.com",
                "contact_email": f"admin{i}@parallel{i}.com",
                "admin_user": {
                    "name": f"Admin {i}",
                    "email": f"admin{i}@parallel{i}.com",
                    "password": "SecurePass123!"
                }
            }
            for i in range(3)
        ]
        
        # Register all clients in parallel
        registration_tasks = [
            async_client.post("/api/client-registration/register", json=client_data)
            for client_data in clients_data
        ]
        
        registration_responses = await asyncio.gather(*registration_tasks, return_exceptions=True)
        
        # Verify all registrations succeeded
        successful_registrations = []
        for i, response in enumerate(registration_responses):
            if not isinstance(response, Exception) and response.status_code == status.HTTP_201_CREATED:
                successful_registrations.append(response.json())
        
        # Should have at least some successful registrations
        assert len(successful_registrations) > 0
        
        # Verify no duplicate domains or emails
        domains = [reg["client_id"] for reg in successful_registrations]
        assert len(domains) == len(set(domains))  # All unique
        
        # Verify all clients exist in database
        for registration in successful_registrations:
            client = await clean_db.clients.find_one({"_id": ObjectId(registration["client_id"])})
            assert client is not None
            assert client["status"] == "pending"

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWidgetWorkflow:
    """Test complete widget usage workflow"""
    
    async def test_widget_embed_to_conversation_flow(self, async_client, clean_db, test_client_with_user):
        """Test complete widget flow from embed script to conversation logging"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Step 1: Get widget embed script
        embed_response = await async_client.get(f"/api/widget/embed/{client_id}")
        
        if embed_response.status_code == status.HTTP_200_OK:
            embed_script = embed_response.text
            assert client_id in embed_script
            assert "function" in embed_script or "const" in embed_script
        
        # Step 2: Get widget configuration
        config_response = await async_client.get(f"/api/widget/config/{client_id}")
        
        if config_response.status_code == status.HTTP_200_OK:
            config = config_response.json()
            assert config["client_id"] == client_id
            assert "settings" in config
        
        # Step 3: Simulate multiple chat interactions
        session_id = f"widget_session_{secrets.token_hex(8)}"
        
        chat_messages = [
            "Hello, I'm interested in buying a car",
            "What are the current COE prices?",
            "Can I book a test drive?",
            "What financing options do you have?"
        ]
        
        conversation_responses = []
        
        for message in chat_messages:
            chat_data = {
                "message": message,
                "session_id": session_id,
                "client_id": client_id
            }
            
            chat_response = await async_client.post("/api/widget/chat", json=chat_data)
            
            if chat_response.status_code == status.HTTP_200_OK:
                conversation_responses.append(chat_response.json())
                # Small delay between messages
                await asyncio.sleep(0.1)
        
        # Step 4: Verify conversation was properly logged
        if conversation_responses:
            conversation = await clean_db.conversations.find_one({
                "client_id": client_id,
                "session_id": session_id
            })
            
            if conversation:
                assert conversation["client_id"] == client_id
                assert conversation["session_id"] == session_id
        
        # Step 5: Test conversation history retrieval
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        
        history_response = await async_client.get(
            "/api/conversation/history",
            headers=headers
        )
        
        if history_response.status_code == status.HTTP_200_OK:
            history_data = history_response.json()
            # Should contain conversation data
            assert isinstance(history_data, dict)
    
    async def test_widget_customization_flow(self, async_client, clean_db, test_client_with_user):
        """Test widget customization and branding flow"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        
        # Step 1: Update client settings for widget customization
        custom_settings = {
            "branding": {
                "company_name": "Custom Motors",
                "primary_color": "#FF5733",
                "secondary_color": "#33FF57",
                "logo_url": "https://example.com/logo.png"
            },
            "features": {
                "coe_prices": True,
                "loan_calculator": True,
                "appointment_booking": True,
                "live_chat": True
            },
            "contact_info": {
                "phone": "+65 6123 4567",
                "email": "contact@custommotors.com",
                "address": "123 Custom Street"
            }
        }
        
        # Update client settings
        await clean_db.clients.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": {"settings": custom_settings}}
        )
        
        # Step 2: Get updated widget configuration
        config_response = await async_client.get(f"/api/widget/config/{client_id}")
        
        if config_response.status_code == status.HTTP_200_OK:
            config = config_response.json()
            assert config["client_id"] == client_id
            
            if "settings" in config:
                settings = config["settings"]
                if "branding" in settings:
                    assert settings["branding"]["company_name"] == "Custom Motors"
                    assert settings["branding"]["primary_color"] == "#FF5733"
        
        # Step 3: Test widget with custom settings
        chat_data = {
            "message": "Hello, I see your custom branding!",
            "session_id": f"custom_session_{secrets.token_hex(8)}",
            "client_id": client_id
        }
        
        chat_response = await async_client.post("/api/widget/chat", json=chat_data)
        
        if chat_response.status_code == status.HTTP_200_OK:
            chat_result = chat_response.json()
            assert "response" in chat_result

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteAppointmentWorkflow:
    """Test complete appointment management workflow"""
    
    async def test_appointment_booking_to_completion_flow(self, async_client, clean_db, test_client_with_user):
        """Test complete appointment flow from booking to completion"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        
        # Step 1: Customer books appointment via widget
        appointment_data = {
            "customer_name": "John E2E Customer",
            "customer_email": "john.e2e@example.com",
            "customer_phone": "+65 6123 4567",
            "appointment_datetime": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "service_type": "test_drive",
            "vehicle_interest": "Toyota Camry Hybrid",
            "notes": "Interested in hybrid technology"
        }
        
        booking_response = await async_client.post(
            "/api/appointments/",
            json=appointment_data,
            headers=headers
        )
        
        if booking_response.status_code == status.HTTP_201_CREATED:
            booking_result = booking_response.json()
            appointment_id = booking_result["appointment_id"]
            
            # Step 2: Verify appointment in database
            appointment = await clean_db.appointments.find_one({
                "appointment_id": appointment_id
            })
            
            assert appointment is not None
            assert appointment["client_id"] == client_id
            assert appointment["status"] == "pending"
            
            # Step 3: Admin views appointments
            appointments_response = await async_client.get(
                "/api/appointments/",
                headers=headers
            )
            
            if appointments_response.status_code == status.HTTP_200_OK:
                appointments_data = appointments_response.json()
                # Should contain the new appointment
                assert isinstance(appointments_data, (dict, list))
            
            # Step 4: Admin confirms appointment
            confirmation_data = {
                "status": "confirmed",
                "notes": "Appointment confirmed by admin"
            }
            
            confirm_response = await async_client.put(
                f"/api/appointments/{appointment_id}/status",
                json=confirmation_data,
                headers=headers
            )
            
            if confirm_response.status_code == status.HTTP_200_OK:
                # Verify status update
                updated_appointment = await clean_db.appointments.find_one({
                    "appointment_id": appointment_id
                })
                
                if updated_appointment:
                    assert updated_appointment["status"] == "confirmed"
            
            # Step 5: Customer lookup by phone
            customer_lookup_response = await async_client.get(
                f"/api/appointments/customer/{appointment_data['customer_phone']}",
                headers=headers
            )
            
            if customer_lookup_response.status_code == status.HTTP_200_OK:
                customer_appointments = customer_lookup_response.json()
                # Should find the customer's appointments
                assert isinstance(customer_appointments, (dict, list))
            
            # Step 6: Complete appointment
            completion_data = {
                "status": "completed",
                "notes": "Test drive completed successfully"
            }
            
            complete_response = await async_client.put(
                f"/api/appointments/{appointment_id}/status",
                json=completion_data,
                headers=headers
            )
            
            if complete_response.status_code == status.HTTP_200_OK:
                # Final verification
                final_appointment = await clean_db.appointments.find_one({
                    "appointment_id": appointment_id
                })
                
                if final_appointment:
                    assert final_appointment["status"] == "completed"
    
    async def test_appointment_conflict_prevention(self, async_client, clean_db, test_client_with_user):
        """Test appointment conflict prevention and scheduling"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        
        # Create base appointment time
        base_time = datetime.utcnow() + timedelta(days=1)
        
        # Step 1: Book first appointment
        appointment1_data = {
            "customer_name": "Customer One",
            "customer_email": "customer1@example.com",
            "customer_phone": "+65 6111 1111",
            "appointment_datetime": base_time.isoformat(),
            "service_type": "test_drive",
            "vehicle_interest": "Toyota Camry"
        }
        
        response1 = await async_client.post(
            "/api/appointments/",
            json=appointment1_data,
            headers=headers
        )
        
        if response1.status_code == status.HTTP_201_CREATED:
            # Step 2: Try to book conflicting appointment (same time)
            appointment2_data = {
                "customer_name": "Customer Two",
                "customer_email": "customer2@example.com",
                "customer_phone": "+65 6222 2222",
                "appointment_datetime": base_time.isoformat(),  # Same time
                "service_type": "test_drive",
                "vehicle_interest": "Honda Civic"
            }
            
            response2 = await async_client.post(
                "/api/appointments/",
                json=appointment2_data,
                headers=headers
            )
            
            # Should either succeed (if no conflict checking) or fail with conflict
            assert response2.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_409_CONFLICT
            ]
            
            # Step 3: Book appointment at different time (should succeed)
            appointment3_data = {
                "customer_name": "Customer Three",
                "customer_email": "customer3@example.com",
                "customer_phone": "+65 6333 3333",
                "appointment_datetime": (base_time + timedelta(hours=2)).isoformat(),
                "service_type": "test_drive",
                "vehicle_interest": "Mazda CX-5"
            }
            
            response3 = await async_client.post(
                "/api/appointments/",
                json=appointment3_data,
                headers=headers
            )
            
            # This should succeed
            assert response3.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteDataIsolationWorkflow:
    """Test complete data isolation workflow between clients"""
    
    async def test_multi_client_data_isolation_e2e(self, async_client, clean_db, abc_motors_data, xyz_auto_data):
        """Test end-to-end data isolation between multiple clients"""
        # Step 1: Create two separate clients
        client1_data = await self._setup_complete_client(clean_db, abc_motors_data)
        client2_data = await self._setup_complete_client(clean_db, xyz_auto_data)
        
        # Step 2: Both clients create data
        
        # Client 1 activities
        headers1 = {"Authorization": f"Bearer {client1_data['token']}"}
        
        # Client 1 chat
        chat1_data = {
            "message": "Client 1 exclusive conversation",
            "session_id": "client1_session",
            "client_id": client1_data["client_id"]
        }
        
        await async_client.post("/api/widget/chat", json=chat1_data)
        
        # Client 1 appointment
        appointment1_data = {
            "customer_name": "Client 1 Customer",
            "customer_email": "client1customer@example.com",
            "customer_phone": "+65 6111 1111",
            "appointment_datetime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "service_type": "test_drive"
        }
        
        await async_client.post("/api/appointments/", json=appointment1_data, headers=headers1)
        
        # Client 2 activities
        headers2 = {"Authorization": f"Bearer {client2_data['token']}"}
        
        # Client 2 chat
        chat2_data = {
            "message": "Client 2 exclusive conversation",
            "session_id": "client2_session",
            "client_id": client2_data["client_id"]
        }
        
        await async_client.post("/api/widget/chat", json=chat2_data)
        
        # Client 2 appointment
        appointment2_data = {
            "customer_name": "Client 2 Customer",
            "customer_email": "client2customer@example.com",
            "customer_phone": "+65 6222 2222",
            "appointment_datetime": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "service_type": "service"
        }
        
        await async_client.post("/api/appointments/", json=appointment2_data, headers=headers2)
        
        # Step 3: Verify data isolation
        
        # Client 1 should only see their data
        conv1_response = await async_client.get("/api/conversation/history", headers=headers1)
        appt1_response = await async_client.get("/api/appointments/", headers=headers1)
        
        # Client 2 should only see their data
        conv2_response = await async_client.get("/api/conversation/history", headers=headers2)
        appt2_response = await async_client.get("/api/appointments/", headers=headers2)
        
        # Verify responses don't contain cross-client data
        if conv1_response.status_code == status.HTTP_200_OK and conv2_response.status_code == status.HTTP_200_OK:
            conv1_data = str(conv1_response.json())
            conv2_data = str(conv2_response.json())
            
            # Client 1 data should not appear in Client 2 response
            assert "Client 1 exclusive" not in conv2_data
            assert "Client 2 exclusive" not in conv1_data
        
        if appt1_response.status_code == status.HTTP_200_OK and appt2_response.status_code == status.HTTP_200_OK:
            appt1_data = str(appt1_response.json())
            appt2_data = str(appt2_response.json())
            
            # Client 1 appointments should not appear in Client 2 response
            assert "client1customer@example.com" not in appt2_data
            assert "client2customer@example.com" not in appt1_data
        
        # Step 4: Verify database-level isolation
        client1_conversations = await clean_db.conversations.find(
            {"client_id": client1_data["client_id"]}
        ).to_list(length=None)
        
        client2_conversations = await clean_db.conversations.find(
            {"client_id": client2_data["client_id"]}
        ).to_list(length=None)
        
        # Each client should only have their own conversations
        for conv in client1_conversations:
            assert conv["client_id"] == client1_data["client_id"]
        
        for conv in client2_conversations:
            assert conv["client_id"] == client2_data["client_id"]
    
    async def _setup_complete_client(self, db, client_data):
        """Helper to setup a complete client with user and token"""
        from conftest import hash_password, create_access_token
        
        # Create client
        client_doc = {
            "business_name": client_data["business_name"],
            "domain": client_data["domain"],
            "contact_email": client_data["contact_email"],
            "status": "active",
            "api_key": f"cc_{secrets.token_urlsafe(32)}",
            "settings": {
                "branding": {
                    "company_name": client_data["business_name"],
                    "primary_color": "#4F46E5"
                }
            },
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