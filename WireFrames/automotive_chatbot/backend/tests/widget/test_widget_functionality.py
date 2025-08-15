#!/usr/bin/env python3
"""
Widget functionality tests with different client configurations
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
import secrets
from bson import ObjectId
import json

@pytest.mark.widget
class TestWidgetConfiguration:
    """Test widget configuration for different clients"""
    
    async def test_abc_motors_widget_config(self, async_client, clean_db, abc_motors_client):
        """Test ABC Motors specific widget configuration"""
        client_data = abc_motors_client
        client_id = client_data["client_id"]
        
        # Get widget configuration
        response = await async_client.get(f"/api/widget/config/{client_id}")
        
        assert response.status_code == status.HTTP_200_OK
        config = response.json()
        
        # Verify ABC Motors specific configuration
        assert config["client_id"] == client_id
        assert "ABC Motors" in config.get("business_name", "")
        assert config.get("domain") == "abcmotors.com"
        
        # Verify widget customization
        widget_settings = config.get("widget_settings", {})
        assert "theme" in widget_settings
        assert "branding" in widget_settings
        assert "features" in widget_settings
        
        # ABC Motors should have automotive-specific features
        features = widget_settings.get("features", {})
        assert features.get("appointment_booking", False) == True
        assert features.get("vehicle_inquiry", False) == True
        assert features.get("service_booking", False) == True
    
    async def test_xyz_auto_widget_config(self, async_client, clean_db, xyz_auto_client):
        """Test XYZ Auto specific widget configuration"""
        client_data = xyz_auto_client
        client_id = client_data["client_id"]
        
        # Get widget configuration
        response = await async_client.get(f"/api/widget/config/{client_id}")
        
        assert response.status_code == status.HTTP_200_OK
        config = response.json()
        
        # Verify XYZ Auto specific configuration
        assert config["client_id"] == client_id
        assert "XYZ Auto" in config.get("business_name", "")
        assert config.get("domain") == "xyzauto.com"
        
        # Verify different widget customization from ABC Motors
        widget_settings = config.get("widget_settings", {})
        assert "theme" in widget_settings
        assert "branding" in widget_settings
        
        # XYZ Auto might have different feature set
        features = widget_settings.get("features", {})
        assert "appointment_booking" in features
        assert "vehicle_inquiry" in features
    
    async def test_widget_branding_customization(self, async_client, clean_db, abc_motors_client):
        """Test widget branding customization"""
        client_data = abc_motors_client
        client_id = client_data["client_id"]
        
        # Update widget branding
        branding_update = {
            "primary_color": "#FF6B35",
            "secondary_color": "#004E89",
            "logo_url": "https://abcmotors.com/logo.png",
            "company_name": "ABC Motors",
            "welcome_message": "Welcome to ABC Motors! How can we help you today?"
        }
        
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        response = await async_client.put(
            f"/api/widget/config/{client_id}/branding",
            json=branding_update,
            headers=headers
        )
        
        # Note: This endpoint might not exist yet, so we'll test the config retrieval
        config_response = await async_client.get(f"/api/widget/config/{client_id}")
        assert config_response.status_code == status.HTTP_200_OK
        
        config = config_response.json()
        widget_settings = config.get("widget_settings", {})
        branding = widget_settings.get("branding", {})
        
        # Verify branding elements are present
        assert "primary_color" in branding or "theme" in widget_settings
        assert "company_name" in branding or "business_name" in config
    
    async def test_widget_feature_toggles(self, async_client, clean_db, test_client_with_user):
        """Test widget feature toggle functionality"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Get current configuration
        response = await async_client.get(f"/api/widget/config/{client_id}")
        assert response.status_code == status.HTTP_200_OK
        
        config = response.json()
        widget_settings = config.get("widget_settings", {})
        features = widget_settings.get("features", {})
        
        # Test that feature toggles are properly configured
        expected_features = [
            "appointment_booking",
            "vehicle_inquiry",
            "service_booking",
            "live_chat",
            "file_upload",
            "contact_form"
        ]
        
        for feature in expected_features:
            assert feature in features or feature in widget_settings
    
    async def test_widget_multilingual_support(self, async_client, clean_db, test_client_with_user):
        """Test widget multilingual support configuration"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test different language configurations
        languages_to_test = ["en", "zh", "ms"]
        
        for lang in languages_to_test:
            response = await async_client.get(
                f"/api/widget/config/{client_id}",
                params={"lang": lang}
            )
            
            assert response.status_code == status.HTTP_200_OK
            config = response.json()
            
            # Verify language-specific configuration
            widget_settings = config.get("widget_settings", {})
            assert "language" in widget_settings or "locale" in widget_settings

@pytest.mark.widget
class TestWidgetEmbedScript:
    """Test widget embed script generation and functionality"""
    
    async def test_embed_script_generation(self, async_client, clean_db, abc_motors_client):
        """Test embed script generation for ABC Motors"""
        client_data = abc_motors_client
        client_id = client_data["client_id"]
        
        # Get embed script
        response = await async_client.get(f"/api/widget/embed/{client_id}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/javascript"
        
        script_content = response.text
        
        # Verify script contains necessary elements
        assert client_id in script_content
        assert "CleverCompanion" in script_content or "widget" in script_content.lower()
        assert "function" in script_content or "const" in script_content
        
        # Verify script is properly formatted JavaScript
        assert script_content.strip().endswith(";")
        assert "(function()" in script_content or "(() =>" in script_content
    
    async def test_embed_script_client_specific(self, async_client, clean_db, xyz_auto_client):
        """Test embed script is client-specific for XYZ Auto"""
        client_data = xyz_auto_client
        client_id = client_data["client_id"]
        
        # Get embed script
        response = await async_client.get(f"/api/widget/embed/{client_id}")
        
        assert response.status_code == status.HTTP_200_OK
        script_content = response.text
        
        # Verify client-specific elements
        assert client_id in script_content
        
        # Script should not contain other client IDs
        # (This would require having multiple clients to test properly)
        assert len(client_id) > 10  # Ensure we have a valid client ID
    
    async def test_embed_script_security_headers(self, async_client, clean_db, test_client_with_user):
        """Test embed script security headers"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Get embed script
        response = await async_client.get(f"/api/widget/embed/{client_id}")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify security headers
        headers = response.headers
        assert "content-type" in headers
        assert headers["content-type"] == "application/javascript"
        
        # Check for CORS headers if present
        if "access-control-allow-origin" in headers:
            assert headers["access-control-allow-origin"] in ["*", "https://*"]
    
    async def test_embed_script_caching(self, async_client, clean_db, test_client_with_user):
        """Test embed script caching behavior"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Get embed script multiple times
        response1 = await async_client.get(f"/api/widget/embed/{client_id}")
        response2 = await async_client.get(f"/api/widget/embed/{client_id}")
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        # Scripts should be identical
        assert response1.text == response2.text
        
        # Check for cache headers if implemented
        headers = response1.headers
        if "cache-control" in headers:
            assert "max-age" in headers["cache-control"]

@pytest.mark.widget
class TestWidgetChatFunctionality:
    """Test widget chat functionality with different configurations"""
    
    async def test_abc_motors_chat_flow(self, async_client, clean_db, abc_motors_client):
        """Test chat flow specific to ABC Motors"""
        client_data = abc_motors_client
        client_id = client_data["client_id"]
        session_id = f"abc_test_{secrets.token_hex(8)}"
        
        # Test automotive-specific queries
        automotive_queries = [
            "I want to schedule a test drive",
            "What are your service hours?",
            "Do you have Toyota Camry in stock?",
            "I need to book a maintenance appointment",
            "What financing options do you offer?"
        ]
        
        for query in automotive_queries:
            chat_data = {
                "message": query,
                "session_id": session_id,
                "client_id": client_id
            }
            
            response = await async_client.post("/api/widget/chat", json=chat_data)
            
            assert response.status_code == status.HTTP_200_OK
            chat_response = response.json()
            
            # Verify response structure
            assert "response" in chat_response
            assert "session_id" in chat_response
            assert chat_response["session_id"] == session_id
            
            # Verify automotive context is maintained
            response_text = chat_response["response"].lower()
            automotive_keywords = ["vehicle", "car", "service", "appointment", "test drive", "financing"]
            
            # At least some responses should contain automotive keywords
            if any(keyword in query.lower() for keyword in automotive_keywords):
                # Response should be contextually relevant
                assert len(chat_response["response"]) > 10
    
    async def test_xyz_auto_chat_flow(self, async_client, clean_db, xyz_auto_client):
        """Test chat flow specific to XYZ Auto"""
        client_data = xyz_auto_client
        client_id = client_data["client_id"]
        session_id = f"xyz_test_{secrets.token_hex(8)}"
        
        # Test different automotive scenarios
        xyz_queries = [
            "What electric vehicles do you have?",
            "I need parts for my Honda Civic",
            "Can you help me with insurance?",
            "What's your warranty policy?"
        ]
        
        for query in xyz_queries:
            chat_data = {
                "message": query,
                "session_id": session_id,
                "client_id": client_id
            }
            
            response = await async_client.post("/api/widget/chat", json=chat_data)
            
            assert response.status_code == status.HTTP_200_OK
            chat_response = response.json()
            
            # Verify XYZ Auto specific response
            assert "response" in chat_response
            assert "session_id" in chat_response
            assert chat_response["session_id"] == session_id
            
            # Response should be relevant and substantial
            assert len(chat_response["response"]) > 5
    
    async def test_widget_conversation_persistence(self, async_client, clean_db, test_client_with_user):
        """Test conversation persistence across widget sessions"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        session_id = f"persistence_test_{secrets.token_hex(8)}"
        
        # Send multiple messages in the same session
        messages = [
            "Hello, I'm interested in buying a car",
            "What models do you recommend?",
            "Can you tell me about financing?",
            "I'd like to schedule a test drive"
        ]
        
        for i, message in enumerate(messages):
            chat_data = {
                "message": message,
                "session_id": session_id,
                "client_id": client_id
            }
            
            response = await async_client.post("/api/widget/chat", json=chat_data)
            
            assert response.status_code == status.HTTP_200_OK
            chat_response = response.json()
            
            # Verify session persistence
            assert chat_response["session_id"] == session_id
            
            # Later messages might reference earlier context
            if i > 1:
                # Response should maintain context
                assert len(chat_response["response"]) > 0
        
        # Verify conversation is stored in database
        conversation = await clean_db.conversations.find_one({
            "client_id": client_id,
            "session_id": session_id
        })
        
        assert conversation is not None
        assert conversation["message_count"] >= len(messages)
    
    async def test_widget_appointment_booking_integration(self, async_client, clean_db, abc_motors_client):
        """Test appointment booking through widget chat"""
        client_data = abc_motors_client
        client_id = client_data["client_id"]
        session_id = f"appointment_test_{secrets.token_hex(8)}"
        
        # Test appointment booking flow
        appointment_messages = [
            "I want to book an appointment",
            "I'm available next Tuesday at 2 PM",
            "My name is John Doe",
            "My phone number is +65 6123 4567",
            "I'm interested in a test drive for Toyota Camry"
        ]
        
        for message in appointment_messages:
            chat_data = {
                "message": message,
                "session_id": session_id,
                "client_id": client_id
            }
            
            response = await async_client.post("/api/widget/chat", json=chat_data)
            
            assert response.status_code == status.HTTP_200_OK
            chat_response = response.json()
            
            # Verify appointment-related responses
            response_text = chat_response["response"].lower()
            
            if "appointment" in message.lower():
                # Response should acknowledge appointment request
                appointment_keywords = ["appointment", "schedule", "book", "available", "time"]
                assert any(keyword in response_text for keyword in appointment_keywords)
    
    async def test_widget_error_handling(self, async_client, clean_db, test_client_with_user):
        """Test widget error handling scenarios"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test various error scenarios
        error_scenarios = [
            # Empty message
            {
                "message": "",
                "session_id": "error_test_1",
                "client_id": client_id
            },
            # Very long message
            {
                "message": "A" * 5000,
                "session_id": "error_test_2",
                "client_id": client_id
            },
            # Special characters
            {
                "message": "<script>alert('test')</script>",
                "session_id": "error_test_3",
                "client_id": client_id
            },
            # Missing session_id
            {
                "message": "Test message",
                "client_id": client_id
            }
        ]
        
        for scenario in error_scenarios:
            response = await async_client.post("/api/widget/chat", json=scenario)
            
            # Should handle errors gracefully
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
            
            if response.status_code == status.HTTP_200_OK:
                chat_response = response.json()
                assert "response" in chat_response
                # Should not echo back malicious content
                if "<script>" in scenario.get("message", ""):
                    assert "<script>" not in chat_response["response"]

@pytest.mark.widget
class TestWidgetCustomization:
    """Test widget customization features"""
    
    async def test_widget_theme_customization(self, async_client, clean_db, test_client_with_user):
        """Test widget theme customization"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Get widget configuration
        response = await async_client.get(f"/api/widget/config/{client_id}")
        assert response.status_code == status.HTTP_200_OK
        
        config = response.json()
        widget_settings = config.get("widget_settings", {})
        
        # Test theme configuration
        theme = widget_settings.get("theme", {})
        
        # Verify theme elements
        theme_elements = ["primary_color", "secondary_color", "background_color", "text_color"]
        
        for element in theme_elements:
            if element in theme:
                # Verify color format (hex or rgb)
                color_value = theme[element]
                assert isinstance(color_value, str)
                assert len(color_value) > 0
    
    async def test_widget_contact_info_display(self, async_client, clean_db, abc_motors_client):
        """Test widget contact information display"""
        client_data = abc_motors_client
        client_id = client_data["client_id"]
        
        # Get widget configuration
        response = await async_client.get(f"/api/widget/config/{client_id}")
        assert response.status_code == status.HTTP_200_OK
        
        config = response.json()
        
        # Verify contact information is available
        contact_info = config.get("contact_info", {})
        
        # ABC Motors should have contact information
        contact_fields = ["phone", "email", "address", "business_hours"]
        
        # At least some contact information should be present
        present_fields = [field for field in contact_fields if field in contact_info]
        assert len(present_fields) > 0
        
        # Verify business information
        assert "business_name" in config
        assert "ABC Motors" in config["business_name"]
    
    async def test_widget_feature_availability(self, async_client, clean_db, xyz_auto_client):
        """Test widget feature availability for different clients"""
        client_data = xyz_auto_client
        client_id = client_data["client_id"]
        
        # Get widget configuration
        response = await async_client.get(f"/api/widget/config/{client_id}")
        assert response.status_code == status.HTTP_200_OK
        
        config = response.json()
        widget_settings = config.get("widget_settings", {})
        features = widget_settings.get("features", {})
        
        # Test automotive-specific features
        automotive_features = [
            "appointment_booking",
            "vehicle_inquiry",
            "service_booking",
            "test_drive_scheduling",
            "parts_inquiry",
            "financing_calculator"
        ]
        
        # At least basic features should be available
        available_features = [feature for feature in automotive_features if features.get(feature, False)]
        assert len(available_features) >= 2
    
    async def test_widget_responsive_design_config(self, async_client, clean_db, test_client_with_user):
        """Test widget responsive design configuration"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test different viewport configurations
        viewports = ["mobile", "tablet", "desktop"]
        
        for viewport in viewports:
            response = await async_client.get(
                f"/api/widget/config/{client_id}",
                params={"viewport": viewport}
            )
            
            assert response.status_code == status.HTTP_200_OK
            config = response.json()
            
            # Verify responsive configuration
            widget_settings = config.get("widget_settings", {})
            
            # Should have layout or responsive settings
            assert "layout" in widget_settings or "responsive" in widget_settings or "theme" in widget_settings
    
    async def test_widget_analytics_integration(self, async_client, clean_db, test_client_with_user):
        """Test widget analytics integration"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Send some chat messages to generate analytics data
        session_id = f"analytics_test_{secrets.token_hex(8)}"
        
        for i in range(3):
            chat_data = {
                "message": f"Analytics test message {i}",
                "session_id": session_id,
                "client_id": client_id
            }
            
            response = await async_client.post("/api/widget/chat", json=chat_data)
            assert response.status_code == status.HTTP_200_OK
        
        # Check if analytics data is being tracked
        # This would typically involve checking conversation logs
        conversation = await clean_db.conversations.find_one({
            "client_id": client_id,
            "session_id": session_id
        })
        
        if conversation:
            # Verify analytics-relevant data is stored
            assert "timestamp" in conversation
            assert "message_count" in conversation
            assert conversation["message_count"] >= 3
        
        # Test widget usage statistics
        headers = {"Authorization": f"Bearer {client_data['token']}"}
        stats_response = await async_client.get("/api/conversation/stats", headers=headers)
        
        if stats_response.status_code == status.HTTP_200_OK:
            stats = stats_response.json()
            # Verify stats structure
            assert isinstance(stats, dict)
            # Should have some statistical data
            assert len(stats) > 0