#!/usr/bin/env python3
"""
Simple Backend Starter
Minimal FastAPI app to test if backend can start
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create simple app
app = FastAPI(title="CleverCompanion Test Backend")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Backend is running!", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "port": 8000}

# Test endpoint for super admin login
@app.post("/api/auth/super-admin-login")
async def test_super_admin_login():
    return {
        "access_token": "test_token",
        "token_type": "bearer",
        "user": {
            "email": "admin@clevercompanion.com",
            "name": "Test Admin",
            "role": "super_admin"
        }
    }

if __name__ == "__main__":
    print("[START] Starting CleverCompanion Simple Backend on port 8000...")
    uvicorn.run(app, host="localhost", port=8000, reload=True)