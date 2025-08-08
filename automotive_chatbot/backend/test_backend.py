#!/usr/bin/env python3
"""
Test Backend Startup
Quick test to see if the backend can start
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    print("[TEST] Testing backend startup...")
    
    # Test imports
    print("1. Testing FastAPI import...")
    import fastapi
    print(f"   [OK] FastAPI {fastapi.__version__}")
    
    print("2. Testing uvicorn import...")
    import uvicorn
    print(f"   [OK] Uvicorn available")
    
    print("3. Testing motor (MongoDB) import...")
    import motor
    print(f"   [OK] Motor available")
    
    print("4. Testing main app import...")
    from api.main import app
    print(f"   [OK] Main app imported successfully")
    
    print("5. Testing MongoDB connection...")
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    
    async def test_db():
        try:
            client = AsyncIOMotorClient("mongodb+srv://darknesscrawler:P%40ssw0rd%211@aichatbot.ygakb6r.mongodb.net/?retryWrites=true&w=majority&appName=AiChatBot")
            await client.admin.command('ping')
            print("   [OK] MongoDB connection successful")
            client.close()
            return True
        except Exception as e:
            print(f"   [ERROR] MongoDB connection failed: {e}")
            return False
    
    db_result = asyncio.run(test_db())
    
    if db_result:
        print("\n[SUCCESS] All tests passed! Backend should start successfully.")
        print("\n[START] Starting backend server...")
        
        # Start the server
        uvicorn.run(app, host="localhost", port=8000, reload=True)
    else:
        print("\n[ERROR] Database connection failed. Check MongoDB Atlas credentials.")
        
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("[TIP] Try: pip install fastapi uvicorn motor")
except Exception as e:
    print(f"[ERROR] Error: {e}")