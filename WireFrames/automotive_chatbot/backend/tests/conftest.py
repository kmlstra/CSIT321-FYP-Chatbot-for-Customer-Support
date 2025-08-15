#!/usr/bin/env python3
"""
Pytest configuration and fixtures for multi-tenant SaaS platform testing
"""

import pytest
import asyncio
import os
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient
import httpx
from faker import Faker
import hashlib
import jwt
import secrets

# Import the FastAPI app
from api.main import app

# Test configuration
TEST_DATABASE_NAME = "automotive_chatbot_saas_test"
TEST_CONNECTION = "mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot"

JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

fake = Faker()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "widget: marks tests as widget functionality tests"
    )

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Database fixtures
@pytest.fixture(scope="session")
async def test_db_client():
    """Create test database client"""
    client = AsyncIOMotorClient(TEST_CONNECTION)
    yield client
    client.close()

@pytest.fixture(scope="session")
async def test_db(test_db_client):
    """Get test database"""
    return test_db_client[TEST_DATABASE_NAME]

@pytest.fixture(scope="function")
async def clean_db(test_db):
    """Clean database before each test"""
    # Clean all collections
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db[collection_name].delete_many({})
    yield test_db
    # Clean after test
    for collection_name in collections:
        await test_db[collection_name].delete_many({})

# HTTP client fixtures
@pytest.fixture(scope="function")
def sync_client():
    """Synchronous test client for FastAPI"""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
async def async_client():
    """Asynchronous test client for FastAPI"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Authentication helpers
def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# Test data factories
@pytest.fixture
def sample_client_data():
    """Generate sample client data"""
    return {
        "business_name": fake.company(),
        "domain": fake.domain_name(),
        "contact_email": fake.email(),
        "admin_user": {
            "name": fake.name(),
            "email": fake.email(),
            "password": "TestPassword123!"
        },
        "contact_info": {
            "phone": fake.phone_number(),
            "address": fake.address(),
            "city": fake.city(),
            "country": "Singapore"
        }
    }

@pytest.fixture
def abc_motors_data():
    """ABC Motors test client data"""
    return {
        "business_name": "ABC Motors",
        "domain": "abcmotors.com",
        "contact_email": "admin@abcmotors.com",
        "admin_user": {
            "name": "John Smith",
            "email": "john@abcmotors.com",
            "password": "ABCMotors123!"
        },
        "contact_info": {
            "phone": "+65 6123 4567",
            "address": "123 Automotive Street",
            "city": "Singapore",
            "country": "Singapore"
        }
    }

@pytest.fixture
def xyz_auto_data():
    """XYZ Auto test client data"""
    return {
        "business_name": "XYZ Auto",
        "domain": "xyzauto.com",
        "contact_email": "admin@xyzauto.com",
        "admin_user": {
            "name": "Jane Doe",
            "email": "jane@xyzauto.com",
            "password": "XYZAuto123!"
        },
        "contact_info": {
            "phone": "+65 6987 6543",
            "address": "456 Car Dealer Road",
            "city": "Singapore",
            "country": "Singapore"
        }
    }

# Authentication fixtures
@pytest.fixture
async def super_admin_token(test_db):
    """Create super admin and return auth token"""
    # Create super admin
    super_admin = {
        "email": "admin@clevercompanion.com",
        "password_hash": hash_password("SuperAdmin123!"),
        "name": "Super Administrator",
        "role": "super_admin",
        "status": "active",
        "created_at": datetime.utcnow(),
        "last_login": None,
        "login_count": 0
    }
    
    result = await test_db.super_admins.insert_one(super_admin)
    
    # Create token
    token_data = {
        "user_id": str(result.inserted_id),
        "email": super_admin["email"],
        "role": "super_admin",
        "type": "super_admin"
    }
    
    return create_access_token(token_data)

@pytest.fixture
async def test_client_with_user(test_db, abc_motors_data):
    """Create test client with admin user and return client data and token"""
    # Generate API key
    api_key = f"cc_{secrets.token_urlsafe(32)}"
    
    # Create client
    client_data = {
        "business_name": abc_motors_data["business_name"],
        "domain": abc_motors_data["domain"],
        "contact_email": abc_motors_data["contact_email"],
        "status": "active",
        "api_key": api_key,
        "settings": {
            "branding": {
                "company_name": abc_motors_data["business_name"],
                "primary_color": "#4F46E5",
                "secondary_color": "#7C3AED",
                "logo_url": None
            },
            "features": {
                "coe_prices": True,
                "loan_calculator": True,
                "appointment_booking": True,
                "maintenance_tips": True,
                "vehicle_search": True,
                "contact_support": True,
                "business_hours": True
            },
            "contact_info": abc_motors_data["contact_info"]
        },
        "subscription": {
            "plan": "professional",
            "status": "active",
            "started_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=365)
        },
        "created_at": datetime.utcnow(),
        "approved_at": datetime.utcnow(),
        "approved_by": "system"
    }
    
    client_result = await test_db.clients.insert_one(client_data)
    client_id = str(client_result.inserted_id)
    
    # Create admin user
    admin_user = {
        "client_id": client_id,
        "name": abc_motors_data["admin_user"]["name"],
        "email": abc_motors_data["admin_user"]["email"],
        "password_hash": hash_password(abc_motors_data["admin_user"]["password"]),
        "role": "admin",
        "status": "active",
        "created_at": datetime.utcnow(),
        "last_login": None,
        "login_count": 0
    }
    
    user_result = await test_db.client_users.insert_one(admin_user)
    user_id = str(user_result.inserted_id)
    
    # Create token
    token_data = {
        "user_id": user_id,
        "client_id": client_id,
        "email": admin_user["email"],
        "role": "admin",
        "type": "client_user"
    }
    
    token = create_access_token(token_data)
    
    return {
        "client_id": client_id,
        "user_id": user_id,
        "token": token,
        "api_key": api_key,
        "client_data": client_data,
        "user_data": admin_user
    }

# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance tests"""
    return {
        "concurrent_users": 10,
        "test_duration": 30,  # seconds
        "ramp_up_time": 5,  # seconds
        "max_response_time": 2000,  # milliseconds
        "success_rate_threshold": 0.95
    }

# Widget testing fixtures
@pytest.fixture
def widget_config():
    """Widget configuration for testing"""
    return {
        "title": "Test Chatbot",
        "subtitle": "How can I help you?",
        "welcome_message": "Welcome to our test chatbot!",
        "primary_color": "#4F46E5",
        "secondary_color": "#7C3AED",
        "position": "bottom-right",
        "size": "medium"
    }

# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_after_test(test_db):
    """Cleanup after each test"""
    yield
    # Clean up test data
    collections = ["clients", "client_users", "super_admins", "conversations", "appointments"]
    for collection_name in collections:
        await test_db[collection_name].delete_many({})