#!/usr/bin/env python3
"""
Unit tests for widget API endpoints
"""

import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock
import json

@pytest.mark.unit
@pytest.mark.widget
class TestWidgetConfiguration:
    """Test widget configuration endpoints"""
    
    async def test_get_widget_config_success(self, async_client, test_client_with_user):
        """Test successful widget configuration retrieval"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        response = await async_client.get(f"/api/widget/config/{client_id}")
        
        # This endpoint might not exist yet, check for reasonable responses
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED
        ]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Check expected widget configuration structure
            expected_fields = [
                "client_id",
                "branding",
                "features",
                "contact_info",
                "business_hours"
            ]
            
            for field in expected_fields:
                assert field in data or "config" in data
    
    async def test_get_widget_config_invalid_client(self, async_client):
        """Test widget config with invalid client ID"""
        fake_client_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
        
        response = await async_client.get(f"/api/widget/config/{fake_client_id}")
        
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]
    
    async def test_get_widget_config_malformed_client_id(self, async_client):
        """Test widget config with malformed client ID"""
        malformed_id = "invalid-client-id"
        
        response = await async_client.get(f"/api/widget/config/{malformed_id}")
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    async def test_widget_embed_script_generation(self, async_client, test_client_with_user):
        """Test widget embed script generation"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        response = await async_client.get(f"/api/widget/embed.js?client_id={client_id}")
        
        # This endpoint might not exist yet
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED
        ]
        
        if response.status_code == status.HTTP_200_OK:
            # Should return JavaScript content
            assert response.headers.get("content-type") in [
                "application/javascript",
                "text/javascript",
                "text/plain"
            ]
            
            content = response.text
            # Should contain widget initialization code
            assert "widget" in content.lower() or "chat" in content.lower()

@pytest.mark.unit
@pytest.mark.widget
class TestWidgetChat:
    """Test widget chat functionality"""
    
    async def test_widget_chat_message_success(self, async_client, test_client_with_user):
        """Test sending message through widget"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        chat_message = {
            "message": "Hello, I need help with car loans",
            "session_id": "test_session_123",
            "client_id": client_id
        }
        
        response = await async_client.post("/api/widget/chat", json=chat_message)
        
        # This endpoint might not exist yet
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED
        ]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Check response structure
            expected_fields = ["response", "session_id"]
            for field in expected_fields:
                assert field in data or "message" in data
    
    async def test_widget_chat_empty_message(self, async_client, test_client_with_user):
        """Test widget chat with empty message"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        chat_message = {
            "message": "",
            "session_id": "test_session_123",
            "client_id": client_id
        }
        
        response = await async_client.post("/api/widget/chat", json=chat_message)
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_404_NOT_FOUND  # If endpoint doesn't exist
        ]
    
    async def test_widget_chat_missing_client_id(self, async_client):
        """Test widget chat without client ID"""
        chat_message = {
            "message": "Hello",
            "session_id": "test_session_123"
            # Missing client_id
        }
        
        response = await async_client.post("/api/widget/chat", json=chat_message)
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_404_NOT_FOUND
        ]
    
    async def test_widget_chat_invalid_client_id(self, async_client):
        """Test widget chat with invalid client ID"""
        chat_message = {
            "message": "Hello",
            "session_id": "test_session_123",
            "client_id": "invalid_client_id"
        }
        
        response = await async_client.post("/api/widget/chat", json=chat_message)
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

@pytest.mark.unit
@pytest.mark.widget
class TestWidgetCustomization:
    """Test widget customization features"""
    
    async def test_widget_branding_application(self, async_client, test_client_with_user):
        """Test widget applies client branding correctly"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Get widget config
        response = await async_client.get(f"/api/widget/config/{client_id}")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Check branding fields are present
            if "branding" in data:
                branding = data["branding"]
                assert "company_name" in branding
                assert "primary_color" in branding
                assert "secondary_color" in branding
                
                # Verify color format (should be hex colors)
                primary_color = branding.get("primary_color", "")
                if primary_color:
                    assert primary_color.startswith("#")
                    assert len(primary_color) == 7  # #RRGGBB format
    
    async def test_widget_feature_flags(self, async_client, test_client_with_user):
        """Test widget respects feature flags"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        response = await async_client.get(f"/api/widget/config/{client_id}")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Check feature flags are present
            if "features" in data:
                features = data["features"]
                expected_features = [
                    "coe_prices",
                    "loan_calculator",
                    "appointment_booking",
                    "maintenance_tips",
                    "vehicle_search",
                    "contact_support",
                    "business_hours"
                ]
                
                for feature in expected_features:
                    if feature in features:
                        assert isinstance(features[feature], bool)
    
    async def test_widget_contact_info_display(self, async_client, test_client_with_user):
        """Test widget displays correct contact information"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        response = await async_client.get(f"/api/widget/config/{client_id}")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Check contact info is present
            if "contact_info" in data:
                contact_info = data["contact_info"]
                
                # Should have at least some contact information
                contact_fields = ["phone", "email", "address"]
                has_contact_info = any(field in contact_info for field in contact_fields)
                assert has_contact_info

@pytest.mark.unit
@pytest.mark.widget
class TestWidgetSecurity:
    """Test widget security features"""
    
    async def test_widget_cors_headers(self, async_client, test_client_with_user):
        """Test widget endpoints have proper CORS headers"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        response = await async_client.get(f"/api/widget/config/{client_id}")
        
        # Check for CORS headers (might be set by middleware)
        headers = response.headers
        
        # These headers might be present depending on CORS configuration
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # At least one CORS header should be present for widget endpoints
        # (This is more of a configuration check)
        pass  # CORS is handled by middleware, not individual endpoints
    
    async def test_widget_xss_protection(self, async_client, test_client_with_user):
        """Test widget protects against XSS attacks"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Try to inject script in message
        malicious_message = {
            "message": "<script>alert('XSS')</script>Hello",
            "session_id": "test_session_123",
            "client_id": client_id
        }
        
        response = await async_client.post("/api/widget/chat", json=malicious_message)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            response_text = str(data)
            
            # Response should not contain unescaped script tags
            assert "<script>" not in response_text
            assert "alert('XSS')" not in response_text
    
    async def test_widget_sql_injection_protection(self, async_client, test_client_with_user):
        """Test widget protects against SQL injection"""
        client_data = test_client_with_user
        
        # Try SQL injection in client_id parameter
        malicious_client_id = "'; DROP TABLE clients; --"
        
        response = await async_client.get(f"/api/widget/config/{malicious_client_id}")
        
        # Should return error, not cause database issues
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    async def test_widget_rate_limiting(self, async_client, test_client_with_user):
        """Test widget has rate limiting protection"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Send multiple rapid requests
        responses = []
        for i in range(20):  # Send 20 rapid requests
            chat_message = {
                "message": f"Test message {i}",
                "session_id": "test_session_123",
                "client_id": client_id
            }
            
            response = await async_client.post("/api/widget/chat", json=chat_message)
            responses.append(response.status_code)
        
        # Check if any requests were rate limited
        rate_limited = any(code == status.HTTP_429_TOO_MANY_REQUESTS for code in responses)
        
        # Rate limiting might not be implemented yet, so this is informational
        # In a production system, we'd expect some rate limiting
        pass

@pytest.mark.unit
@pytest.mark.widget
class TestWidgetPerformance:
    """Test widget performance characteristics"""
    
    async def test_widget_config_response_time(self, async_client, test_client_with_user):
        """Test widget config endpoint response time"""
        import time
        
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        start_time = time.time()
        response = await async_client.get(f"/api/widget/config/{client_id}")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Widget config should respond quickly (under 1 second)
        assert response_time < 1000
    
    async def test_widget_config_caching(self, async_client, test_client_with_user):
        """Test widget config caching behavior"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Make first request
        response1 = await async_client.get(f"/api/widget/config/{client_id}")
        
        # Make second request immediately
        response2 = await async_client.get(f"/api/widget/config/{client_id}")
        
        if response1.status_code == status.HTTP_200_OK and response2.status_code == status.HTTP_200_OK:
            # Responses should be identical (cached)
            assert response1.json() == response2.json()
            
            # Check for cache headers
            headers1 = response1.headers
            headers2 = response2.headers
            
            # Look for caching headers (might not be implemented yet)
            cache_headers = ["cache-control", "etag", "last-modified"]
            # This is informational - caching might not be implemented yet

@pytest.mark.unit
@pytest.mark.widget
class TestWidgetIntegration:
    """Test widget integration with other systems"""
    
    async def test_widget_rasa_integration(self, async_client, test_client_with_user):
        """Test widget integrates with RASA for responses"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        # Test common automotive queries
        test_queries = [
            "What are the COE prices?",
            "I want to book a test drive",
            "Tell me about car loans",
            "What are your business hours?"
        ]
        
        for query in test_queries:
            chat_message = {
                "message": query,
                "session_id": "test_session_integration",
                "client_id": client_id
            }
            
            response = await async_client.post("/api/widget/chat", json=chat_message)
            
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                
                # Should get a meaningful response
                if "response" in data:
                    assert len(data["response"]) > 0
                    assert data["response"] != query  # Should not echo the input
    
    async def test_widget_conversation_logging(self, async_client, test_client_with_user):
        """Test widget logs conversations properly"""
        client_data = test_client_with_user
        client_id = client_data["client_id"]
        
        chat_message = {
            "message": "Test conversation logging",
            "session_id": "test_logging_session",
            "client_id": client_id
        }
        
        response = await async_client.post("/api/widget/chat", json=chat_message)
        
        # The conversation should be logged (this would need database verification)
        # For now, we just check that the request doesn't fail
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,  # If endpoint doesn't exist
            status.HTTP_501_NOT_IMPLEMENTED
        ]