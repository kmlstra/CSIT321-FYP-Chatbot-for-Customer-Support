"""
Client Dashboard API Routes
Handles client-specific configuration and management
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

from ..auth.client_auth import (
    get_current_client_user, 
    get_current_client_id,
    require_client_admin,
    require_client_manager
)
from ..config.mongodb_security import get_admin_db, get_security_manager

router = APIRouter(prefix="/api/client", tags=["client-dashboard"])

# Pydantic models for requests
class BrandingUpdate(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = "#4F46E5"
    secondary_color: str = "#7C3AED"
    company_name: str
    favicon_url: Optional[str] = None

class ContactInfoUpdate(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    whatsapp: Optional[str] = None
    website: Optional[str] = None

class BusinessHoursUpdate(BaseModel):
    monday: str = "9:00 AM - 6:00 PM"
    tuesday: str = "9:00 AM - 6:00 PM"
    wednesday: str = "9:00 AM - 6:00 PM"
    thursday: str = "9:00 AM - 6:00 PM"
    friday: str = "9:00 AM - 6:00 PM"
    saturday: str = "9:00 AM - 5:00 PM"
    sunday: str = "Closed"

class FeaturesUpdate(BaseModel):
    coe_prices: bool = True
    loan_calculator: bool = True
    test_drive_booking: bool = True
    maintenance_tips: bool = True
    vehicle_search: bool = True
    contact_support: bool = True
    business_hours: bool = True

class VehicleCreate(BaseModel):
    brand: str
    model: str
    year: int
    price: float
    coe_category: str
    availability: str = "in_stock"
    engine_capacity: Optional[float] = None
    fuel_type: str = "Petrol"
    transmission: str = "Automatic"
    mileage: Optional[int] = None
    features: List[str] = []
    images: List[str] = []
    description: Optional[str] = None

class VehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    coe_category: Optional[str] = None
    availability: Optional[str] = None
    engine_capacity: Optional[float] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    mileage: Optional[int] = None
    features: Optional[List[str]] = None
    images: Optional[List[str]] = None
    description: Optional[str] = None

# Dashboard Overview
@router.get("/dashboard")
async def get_dashboard_overview(
    current_user: Dict[str, Any] = Depends(get_current_client_user),
    database = Depends(get_admin_db),
    security_manager = Depends(get_security_manager)
):
    """Get dashboard overview with metrics"""
    
    client_id = current_user["client"]["id"]
    
    try:
        # Get conversation metrics
        conversations = await security_manager.get_client_specific_data(
            client_id, "conversations"
        )
        
        # Get vehicle count
        vehicles = await security_manager.get_client_specific_data(
            client_id, "client_vehicles"
        )
        
        # Calculate metrics
        total_conversations = len(conversations)
        total_vehicles = len(vehicles)
        
        # Get recent conversations
        recent_conversations = sorted(
            conversations, 
            key=lambda x: x.get("created_at", datetime.min), 
            reverse=True
        )[:5]
        
        return {
            "client": current_user["client"],
            "metrics": {
                "total_conversations": total_conversations,
                "total_vehicles": total_vehicles,
                "active_sessions": len([c for c in conversations if c.get("ended_at") is None]),
                "this_month_conversations": len([
                    c for c in conversations 
                    if c.get("created_at", datetime.min).month == datetime.now().month
                ])
            },
            "recent_conversations": recent_conversations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )

# Branding Configuration
@router.get("/branding")
async def get_branding_config(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
):
    """Get current branding configuration"""
    return current_user["client"]["settings"].get("branding", {})

@router.put("/branding")
async def update_branding_config(
    branding: BrandingUpdate,
    current_user: Dict[str, Any] = Depends(require_client_admin),
    database = Depends(get_admin_db)
):
    """Update branding configuration"""
    
    client_id = current_user["client"]["id"]
    
    try:
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.branding": branding.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return {"message": "Branding updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update branding: {str(e)}"
        )

# Contact Information
@router.get("/contact-info")
async def get_contact_info(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
):
    """Get current contact information"""
    return current_user["client"]["settings"].get("contact_info", {})

@router.put("/contact-info")
async def update_contact_info(
    contact_info: ContactInfoUpdate,
    current_user: Dict[str, Any] = Depends(require_client_manager),
    database = Depends(get_admin_db)
):
    """Update contact information"""
    
    client_id = current_user["client"]["id"]
    
    try:
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.contact_info": contact_info.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return {"message": "Contact information updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact info: {str(e)}"
        )

# Business Hours
@router.get("/business-hours")
async def get_business_hours(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
):
    """Get current business hours"""
    return current_user["client"]["settings"].get("business_hours", {})

@router.put("/business-hours")
async def update_business_hours(
    business_hours: BusinessHoursUpdate,
    current_user: Dict[str, Any] = Depends(require_client_manager),
    database = Depends(get_admin_db)
):
    """Update business hours"""
    
    client_id = current_user["client"]["id"]
    
    try:
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.business_hours": business_hours.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Business hours updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update business hours: {str(e)}"
        )

# Features Configuration
@router.get("/features")
async def get_features_config(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
):
    """Get current features configuration"""
    return current_user["client"]["settings"].get("features", {})

@router.put("/features")
async def update_features_config(
    features: FeaturesUpdate,
    current_user: Dict[str, Any] = Depends(require_client_admin),
    database = Depends(get_admin_db)
):
    """Update features configuration"""
    
    client_id = current_user["client"]["id"]
    
    try:
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.features": features.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Features updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update features: {str(e)}"
        )

# Vehicle Management
@router.get("/vehicles")
async def get_client_vehicles(
    current_user: Dict[str, Any] = Depends(get_current_client_user),
    security_manager = Depends(get_security_manager)
):
    """Get all vehicles for the client"""
    
    client_id = current_user["client"]["id"]
    
    try:
        vehicles = await security_manager.get_client_specific_data(
            client_id, "client_vehicles"
        )
        return {"vehicles": vehicles}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vehicles: {str(e)}"
        )

@router.post("/vehicles")
async def create_vehicle(
    vehicle: VehicleCreate,
    current_user: Dict[str, Any] = Depends(require_client_manager),
    security_manager = Depends(get_security_manager)
):
    """Create a new vehicle"""
    
    client_id = current_user["client"]["id"]
    
    try:
        vehicle_data = vehicle.dict()
        vehicle_data["created_at"] = datetime.utcnow()
        vehicle_data["updated_at"] = datetime.utcnow()
        
        vehicle_id = await security_manager.insert_client_data(
            client_id, "client_vehicles", vehicle_data
        )
        
        return {"message": "Vehicle created successfully", "vehicle_id": vehicle_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vehicle: {str(e)}"
        )

@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: str,
    vehicle: VehicleUpdate,
    current_user: Dict[str, Any] = Depends(require_client_manager),
    security_manager = Depends(get_security_manager)
):
    """Update a vehicle"""
    
    client_id = current_user["client"]["id"]
    
    try:
        update_data = {k: v for k, v in vehicle.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        success = await security_manager.update_client_specific_data(
            client_id, "client_vehicles", vehicle_id, update_data
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return {"message": "Vehicle updated successfully"}
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vehicle: {str(e)}"
        )

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    current_user: Dict[str, Any] = Depends(require_client_admin),
    security_manager = Depends(get_security_manager)
):
    """Delete a vehicle"""
    
    client_id = current_user["client"]["id"]
    
    try:
        success = await security_manager.delete_client_data(
            client_id, "client_vehicles", vehicle_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return {"message": "Vehicle deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vehicle: {str(e)}"
        )

# Analytics
@router.get("/analytics")
async def get_client_analytics(
    current_user: Dict[str, Any] = Depends(get_current_client_user),
    security_manager = Depends(get_security_manager)
):
    """Get analytics for the client"""
    
    client_id = current_user["client"]["id"]
    
    try:
        # Get conversations for analytics
        conversations = await security_manager.get_client_specific_data(
            client_id, "conversations"
        )
        
        # Calculate analytics
        total_conversations = len(conversations)
        unique_users = len(set(c.get("user_id") for c in conversations if c.get("user_id")))
        
        # Monthly breakdown
        monthly_conversations = {}
        for conv in conversations:
            created_at = conv.get("created_at", datetime.min)
            month_key = created_at.strftime("%Y-%m")
            monthly_conversations[month_key] = monthly_conversations.get(month_key, 0) + 1
        
        return {
            "total_conversations": total_conversations,
            "unique_users": unique_users,
            "monthly_conversations": monthly_conversations,
            "avg_messages_per_conversation": sum(c.get("total_messages", 0) for c in conversations) / max(total_conversations, 1)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )

# Embed Code Generation
@router.get("/embed-code")
async def get_embed_code(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
):
    """Get embed code for the client's website"""
    
    client = current_user["client"]
    
    embed_code = f"""<!-- CleverCompanion Automotive Chatbot Widget -->
<script>
  window.CleverCompanionConfig = {{
    clientId: '{client["id"]}',
    apiUrl: 'https://your-domain.com/api/widget',
    apiKey: '{client.get("api_key", "")}',
    domain: '{client["domain"]}'
  }};
</script>
<script src="https://your-domain.com/widget/clevercompanion-widget.js" async></script>
<!-- End CleverCompanion Widget -->"""
    
    return {
        "client_id": client["id"],
        "embed_code": embed_code.strip(),
        "instructions": [
            "Copy the embed code above",
            "Paste it before the closing </body> tag on your website",
            "The chatbot will automatically appear on your site",
            "Customize appearance in the Branding section"
        ],
        "test_url": f"https://your-domain.com/widget/test?client_id={client['id']}"
    }