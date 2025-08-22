"""
Client Dashboard API Routes
Handles client-specific configuration and management
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
import pytz
from bson import ObjectId

from ..auth.client_auth import (
    get_current_client_user, 
    get_current_client_id,
    require_client_admin,
    require_client_manager
)
from ..config.database import get_real_admin_db, get_security_manager

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
    public_holidays: str = "Closed"

class FeaturesUpdate(BaseModel):
    coe_prices: bool = True
    loan_calculator: bool = True
    appointment_booking: bool = True
    vehicle_search: bool = True
    live_support: bool = True
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
    database = Depends(get_real_admin_db),
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

# Conversations endpoint
@router.get("/conversations")
async def get_client_conversations(
    current_user: Dict[str, Any] = Depends(get_current_client_user),
    security_manager = Depends(get_security_manager)
):
    """Get all conversations for the client"""
    
    client_id = current_user["client"]["id"]
    
    try:
        conversations = await security_manager.get_client_specific_data(
            client_id, "conversations"
        )
        
        # Format conversations for frontend
        formatted_conversations = []
        for conv in conversations:
            formatted_conv = {
                "_id": str(conv.get("_id", "")),
                "customer_name": conv.get("customer_name") or conv.get("user_name") or f"Customer {str(conv.get('_id', ''))[:8]}",
                "messages": conv.get("total_messages") or len(conv.get("messages", [])),
                "status": conv.get("status") or "completed",
                "created_at": conv.get("created_at", datetime.now(pytz.timezone('Asia/Singapore'))).isoformat() if isinstance(conv.get("created_at"), datetime) else str(conv.get("created_at", "")),
                "last_message": ""
            }
            
            # Extract last message
            if conv.get("messages") and isinstance(conv["messages"], list) and len(conv["messages"]) > 0:
                last_msg = conv["messages"][-1]
                if isinstance(last_msg, dict):
                    formatted_conv["last_message"] = last_msg.get("content", "")[:50]
            
            formatted_conversations.append(formatted_conv)
        
        return {"conversations": formatted_conversations}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )

# Conversation Details endpoint
@router.get("/conversations/{conversation_id}")
async def get_conversation_details(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_client_user),
    security_manager = Depends(get_security_manager)
):
    """Get detailed conversation messages for a specific conversation"""
    
    client_id = current_user["client"]["id"]
    
    try:
        # Get all messages for this conversation_id
        query_conditions = [
            {"conversation_id": conversation_id},
            {"session_id": conversation_id}
        ]
        
        # Only add ObjectId query if conversation_id is a valid ObjectId
        if ObjectId.is_valid(conversation_id):
            query_conditions.append({"_id": ObjectId(conversation_id)})
        
        # Find all messages for this conversation
        messages_cursor = security_manager.db.unified_conversations.find({
            "client_id": client_id,
            "$or": query_conditions
        }).sort("timestamp", 1)  # Sort by timestamp ascending
        
        messages = await messages_cursor.to_list(length=None)
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Convert ObjectId to string and format messages
        formatted_messages = []
        conversation_info = None
        
        for msg in messages:
            if "_id" in msg:
                msg["_id"] = str(msg["_id"])
            
            # Format message for frontend
            message_type = msg.get("message_type", "user")
            # Map message_type to role for frontend compatibility
            # Ensure proper role mapping: user messages -> "user", assistant/bot messages -> "assistant"
            if message_type.lower() in ["user", "customer"]:
                role = "user"
            elif message_type.lower() in ["assistant", "bot", "system"]:
                role = "assistant"
            else:
                # Default fallback - if message_type is unclear, default to user for safety
                role = "user"
            
            formatted_msg = {
                "id": msg.get("message_id", str(msg.get("_id", ""))),
                "content": msg.get("message", ""),
                "type": message_type,  # Keep original type for backward compatibility
                "role": role,  # Add role field for frontend Dashboard
                "timestamp": msg.get("timestamp"),
                "metadata": msg.get("metadata", {})
            }
            formatted_messages.append(formatted_msg)
            
            # Use first message to get conversation info
            if conversation_info is None:
                conversation_info = {
                    "conversation_id": msg.get("conversation_id", conversation_id),
                    "session_id": msg.get("session_id"),
                    "client_id": msg.get("client_id"),
                    "created_at": msg.get("created_at") or msg.get("timestamp"),
                    "updated_at": messages[-1].get("timestamp") if messages else msg.get("timestamp")
                }
        
        # Create conversation object with messages array
        conversation = {
            **conversation_info,
            "messages": formatted_messages,
            "total_messages": len(formatted_messages)
        }
        
        # Return the conversation with messages
        return {
            "success": True,
            "conversation": conversation
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversation details: {str(e)}"
        )

# Branding Configuration
@router.get("/branding")
async def get_branding_config(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
):
    """Get current branding configuration"""
    branding = current_user["client"]["settings"].get("branding", {})
    return {"branding": branding}

@router.put("/branding")
async def update_branding_config(
    branding: BrandingUpdate,
    current_user: Dict[str, Any] = Depends(require_client_admin),
    database = Depends(get_real_admin_db)
):
    """Update branding configuration"""
    
    client_id = current_user["client"]["id"]
    
    try:
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.branding": branding.dict(),
                    "updated_at": datetime.now(pytz.timezone('Asia/Singapore'))
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
    contact_info = current_user["client"]["settings"].get("contact_info", {})
    return {"contact_info": contact_info}

@router.put("/contact-info")
async def update_contact_info(
    contact_info: ContactInfoUpdate,
    current_user: Dict[str, Any] = Depends(require_client_manager),
    database = Depends(get_real_admin_db)
):
    """Update contact information"""
    
    client_id = current_user["client"]["id"]
    
    try:
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.contact_info": contact_info.dict(),
                    "updated_at": datetime.now(pytz.timezone('Asia/Singapore'))
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

# Operating Hours (alias for business hours to match frontend API calls)
@router.get("/operating-hours")
async def get_operating_hours(
    current_user: Dict[str, Any] = Depends(get_current_client_user)
):
    """Get current operating hours (alias for business hours)"""
    business_hours = current_user["client"]["settings"].get("business_hours", {})
    
    # Convert business hours format to operating hours format expected by frontend
    operating_hours = {}
    for day, hours in business_hours.items():
        if isinstance(hours, str):
            if hours.lower() == "closed":
                operating_hours[day] = {"open": "09:00", "close": "18:00", "closed": True}
            else:
                # Parse "9:00 AM - 6:00 PM" format
                try:
                    parts = hours.split(" - ")
                    if len(parts) == 2:
                        open_part = parts[0].strip()
                        close_part = parts[1].strip()
                        
                        # Extract time and AM/PM
                        open_time = open_part.replace(" AM", "").replace(" PM", "")
                        close_time = close_part.replace(" AM", "").replace(" PM", "")
                        
                        # Convert to 24-hour format with proper padding
                        def to_24_hour(time_str, period):
                            try:
                                hour, minute = time_str.split(":")
                                hour = int(hour)
                                if period == "AM":
                                    if hour == 12:
                                        hour = 0
                                else:  # PM
                                    if hour != 12:
                                        hour += 12
                                return f"{hour:02d}:{minute}"
                            except:
                                return "09:00"
                        
                        open_period = "AM" if "AM" in open_part else "PM"
                        close_period = "AM" if "AM" in close_part else "PM"
                        
                        open_time_24 = to_24_hour(open_time, open_period)
                        close_time_24 = to_24_hour(close_time, close_period)
                        
                        operating_hours[day] = {"open": open_time_24, "close": close_time_24, "closed": False}
                    else:
                        operating_hours[day] = {"open": "09:00", "close": "18:00", "closed": False}
                except:
                    operating_hours[day] = {"open": "09:00", "close": "18:00", "closed": False}
        else:
            operating_hours[day] = {"open": "09:00", "close": "18:00", "closed": False}
    
    return {"operating_hours": operating_hours}

@router.put("/operating-hours")
async def update_operating_hours(
    operating_hours: dict,
    current_user: Dict[str, Any] = Depends(require_client_manager),
    database = Depends(get_real_admin_db)
):
    """Update operating hours (converts to business hours format)"""
    
    client_id = current_user["client"]["id"]
    
    try:
        # Convert operating hours format to business hours format
        business_hours = {}
        for day, hours in operating_hours.get("operating_hours", {}).items():
            if hours.get("closed", False):
                business_hours[day] = "Closed"
            else:
                open_time = hours.get("open", "09:00")
                close_time = hours.get("close", "18:00")
                
                # Convert to 12-hour format
                def to_12_hour(time_str):
                    try:
                        hour, minute = time_str.split(":")
                        hour = int(hour)
                        if hour == 0:
                            return f"12:{minute} AM"
                        elif hour < 12:
                            # Ensure single digit hours don't have leading zero in 12-hour format
                            return f"{hour}:{minute} AM"
                        elif hour == 12:
                            return f"12:{minute} PM"
                        else:
                            display_hour = hour - 12
                            return f"{display_hour}:{minute} PM"
                    except:
                        return "9:00 AM"
                
                business_hours[day] = f"{to_12_hour(open_time)} - {to_12_hour(close_time)}"
        
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.business_hours": business_hours,
                    "updated_at": datetime.now(pytz.timezone('Asia/Singapore'))
                }
            }
        )
        
        return {"message": "Operating hours updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update operating hours: {str(e)}"
        )

@router.put("/business-hours")
async def update_business_hours(
    business_hours: BusinessHoursUpdate,
    current_user: Dict[str, Any] = Depends(require_client_manager),
    database = Depends(get_real_admin_db)
):
    """Update business hours"""
    
    client_id = current_user["client"]["id"]
    
    try:
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.business_hours": business_hours.dict(),
                    "updated_at": datetime.now(pytz.timezone('Asia/Singapore'))
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
    features = current_user["client"]["settings"].get("features", {})
    return {"features": features}

@router.put("/features")
async def update_features_config(
    features: FeaturesUpdate,
    current_user: Dict[str, Any] = Depends(require_client_admin),
    database = Depends(get_real_admin_db)
):
    """Update features configuration"""
    
    client_id = current_user["client"]["id"]
    
    try:
        result = await database.clients.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "settings.features": features.dict(),
                    "updated_at": datetime.now(pytz.timezone('Asia/Singapore'))
                }
            }
        )
        
        # Clear feature cache to ensure immediate effect
        try:
            from api.cache.feature_cache_manager import get_feature_cache_manager
            cache_manager = get_feature_cache_manager()
            cache_manager.invalidate_client(client_id)
        except Exception as cache_error:
            print(f"Warning: Failed to clear feature cache: {cache_error}")
        
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
        vehicle_data["created_at"] = datetime.now(pytz.timezone('Asia/Singapore'))
        vehicle_data["updated_at"] = datetime.now(pytz.timezone('Asia/Singapore'))
        
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
        update_data["updated_at"] = datetime.now(pytz.timezone('Asia/Singapore'))
        
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
    
    # Get the actual API URL from environment or use default
    import os
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    embed_code = f"""<!-- CleverCompanion Chatbot Widget -->
<script>window.CleverCompanionConfig = {{ clientId: '{client["id"]}' }};</script>
<script async>
    // Force use AWS server for backend services (RASA and API)
    // Frontend runs on localhost:3000, but backend services are on AWS
    window.DOMAIN = 'http://13.215.240.173';
    
    // Dynamically load scripts with domain configuration and cache-busting
    const timestamp = Date.now();
    const script1 = document.createElement('script');
    script1.src = window.DOMAIN + ':8000/clevercompanion-widget.js?v=' + timestamp;
    script1.async = true;
    document.head.appendChild(script1);
    
    const script2 = document.createElement('script');
    script2.src = window.DOMAIN + ':8000/page-interactions.js?v=' + timestamp;
    script2.async = true;
    document.head.appendChild(script2);
</script>
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
        "test_url": f"{api_url}/test-client-widget.html?client_id={client['id']}"
    }

# Database Status
@router.get("/database/status")
async def get_database_status(
    current_user: Dict[str, Any] = Depends(get_current_client_user),
    database = Depends(get_real_admin_db)
):
    """Get database connection status for the client"""
    
    client_id = current_user["client"]["id"]
    
    try:
        # Check if client exists in database
        client = await database.clients.find_one({"_id": ObjectId(client_id)})
        
        if not client:
            return {
                "status": "disconnected",
                "message": "Client not found in database",
                "connected": False
            }
        
        # Check database connectivity
        await database.command("ping")
        
        return {
            "status": "connected",
            "message": "Database connection is healthy",
            "connected": True,
            "client_id": client_id,
            "last_updated": client.get("updated_at", client.get("created_at")).isoformat() if client.get("updated_at") or client.get("created_at") else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection error: {str(e)}",
            "connected": False
        }