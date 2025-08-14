"""
Client Registration API Routes
Handles new client signup and account creation
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime

from ..client_management.client_crud import ClientCRUD
from ..config.database import get_real_admin_db

router = APIRouter()

class ClientRegistrationRequest(BaseModel):
    business_name: str
    domain: str
    contact_email: EmailStr
    admin_user: Dict[str, str]  # name, email, password
    contact_info: Dict[str, str] = {}  # phone, address

class RegistrationResponse(BaseModel):
    success: bool
    client_id: str
    message: str
    next_steps: list

@router.post("/client-registration/register", response_model=RegistrationResponse)
async def register_new_client(
    registration: ClientRegistrationRequest,
    database = Depends(get_real_admin_db)
):
    """Register a new automotive business client"""
    
    try:
        client_crud = ClientCRUD(database)
        
        # Prepare client data
        client_data = {
            "business_name": registration.business_name,
            "domain": registration.domain,
            "contact_email": registration.contact_email,
            "subscription_plan": "premium",  # All features available since payment is external
            "admin_user": registration.admin_user,
            "settings": {
                "branding": {
                    "company_name": registration.business_name,
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
                "contact_info": registration.contact_info,
                "business_hours": {
                    "monday": "9:00 AM - 6:00 PM",
                    "tuesday": "9:00 AM - 6:00 PM",
                    "wednesday": "9:00 AM - 6:00 PM",
                    "thursday": "9:00 AM - 6:00 PM",
                    "friday": "9:00 AM - 6:00 PM",
                    "saturday": "9:00 AM - 5:00 PM",
                    "sunday": "Closed"
                }
            }
        }
        
        # Create client account
        result = await client_crud.create_client(client_data)
        
        return RegistrationResponse(
            success=True,
            client_id=result["client_id"],
            message="Account created successfully! Awaiting admin approval.",
            next_steps=[
                "Your account has been created with 'pending' status",
                "Our team will review and activate your account within 24 hours",
                "You'll receive an email confirmation once approved",
                "Then you can log in and configure your chatbot",
                "Get your embed code to add the chatbot to your website"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/client-registration/status/{client_id}")
async def check_registration_status(
    client_id: str,
    database = Depends(get_real_admin_db)
):
    """Check the status of a client registration"""
    
    try:
        client_crud = ClientCRUD(database)
        client = await client_crud.get_client(client_id)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return {
            "client_id": client_id,
            "business_name": client["business_name"],
            "status": client["status"],
            "created_at": client["created_at"],
            "activated_at": client.get("activated_at"),
            "message": {
                "pending": "Your account is pending approval",
                "active": "Your account is active and ready to use",
                "suspended": "Your account has been suspended",
                "cancelled": "Your account has been cancelled"
            }.get(client["status"], "Unknown status")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )