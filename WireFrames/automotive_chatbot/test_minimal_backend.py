#!/usr/bin/env python3
"""
Minimal Backend Test - No dependencies except FastAPI
"""

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    app = FastAPI(title="Minimal Test Backend")
    
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
        return {"message": "Minimal backend is working!", "status": "ok"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    # Test super admin login endpoint
    @app.post("/api/auth/super-admin-login")
    async def test_super_admin_login():
        return {
            "access_token": "test_token_12345",
            "token_type": "bearer",
            "user": {
                "email": "admin@clevercompanion.com",
                "name": "Test Admin",
                "role": "super_admin"
            }
        }
    
    # Test client login endpoint
    @app.post("/api/auth/client-login")
    async def test_client_login():
        return {
            "access_token": "client_test_token_12345",
            "token_type": "bearer",
            "user": {
                "id": "user_123",
                "email": "admin@abcmotors.com.sg",
                "name": "John Tan",
                "role": "admin",
                "client_id": "client_123"
            },
            "client": {
                "id": "client_123",
                "business_name": "ABC Motors Singapore",
                "domain": "abcmotors.com.sg",
                "status": "active",
                "settings": {
                    "branding": {
                        "company_name": "ABC Motors Singapore",
                        "primary_color": "#4F46E5",
                        "secondary_color": "#7C3AED"
                    },
                    "features": {
                        "coe_prices": True,
                        "loan_calculator": True,
                        "test_drive_booking": True,
                        "maintenance_tips": True,
                        "vehicle_search": True,
                        "contact_support": True
                    },
                    "contact_info": {
                        "phone": "+65 6234 5678",
                        "email": "sales@abcmotors.com.sg",
                        "address": "123 Automotive Street, Singapore"
                    }
                }
            }
        }
    
    # Test client registration endpoint
    @app.post("/api/client-registration/register")
    async def test_client_registration(request_data: dict):
        return {
            "success": True,
            "client_id": "test_client_123",
            "message": "Account created successfully! Awaiting approval.",
            "next_steps": [
                "Your account has been created with 'pending' status",
                "Our team will review and activate your account within 24 hours",
                "You'll receive an email confirmation once approved",
                "Then you can log in and configure your chatbot"
            ]
        }
    
    # Test client dashboard endpoint
    @app.get("/api/client/dashboard")
    async def test_client_dashboard():
        return {
            "client": {
                "id": "client_123",
                "business_name": "ABC Motors Singapore",
                "domain": "abcmotors.com.sg",
                "status": "active",
                "settings": {
                    "branding": {
                        "company_name": "ABC Motors Singapore",
                        "primary_color": "#4F46E5",
                        "secondary_color": "#7C3AED"
                    },
                    "features": {
                        "coe_prices": True,
                        "loan_calculator": True,
                        "test_drive_booking": True,
                        "maintenance_tips": True,
                        "vehicle_search": True,
                        "contact_support": True
                    }
                }
            },
            "metrics": {
                "total_conversations": 156,
                "total_vehicles": 12,
                "active_sessions": 3,
                "this_month_conversations": 45
            }
        }
    
    # Test super admin endpoints
    @app.get("/api/super-admin/clients")
    async def test_get_clients():
        return [
            {
                "id": "client_123",
                "business_name": "ABC Motors Singapore",
                "domain": "abcmotors.com.sg",
                "contact_email": "admin@abcmotors.com.sg",
                "status": "active",
                "subscription_plan": {
                    "plan_type": "premium",
                    "price_per_month": 299.0
                },
                "created_at": "2025-01-15T10:30:00Z",
                "current_month_conversations": 45,
                "total_conversations": 156
            },
            {
                "id": "client_456",
                "business_name": "XYZ Automotive",
                "domain": "xyzauto.com.sg",
                "contact_email": "admin@xyzauto.com.sg",
                "status": "pending",
                "subscription_plan": {
                    "plan_type": "basic",
                    "price_per_month": 99.0
                },
                "created_at": "2025-01-15T14:20:00Z",
                "current_month_conversations": 0,
                "total_conversations": 0
            }
        ]
    
    @app.post("/api/super-admin/clients/{client_id}/approve")
    async def test_approve_client(client_id: str):
        return {
            "success": True,
            "message": f"Client {client_id} approved successfully",
            "client_id": client_id
        }
    
    @app.get("/api/super-admin/metrics")
    async def test_get_metrics():
        return {
            "total_clients": 2,
            "active_clients": 1,
            "pending_approvals": 1,
            "total_conversations_today": 23,
            "revenue_this_month": 299.0,
            "system_uptime": 99.9
        }
    
    if __name__ == "__main__":
        print("🚀 Starting minimal backend on port 8000...")
        uvicorn.run(app, host="localhost", port=8000, reload=False)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Try: pip install fastapi uvicorn")
except Exception as e:
    print(f"❌ Error: {e}")