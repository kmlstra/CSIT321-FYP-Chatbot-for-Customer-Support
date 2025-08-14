
"""
Multi-tenant Chat API - Routes chat requests to correct client context
Handles widget chat requests with client-specific data and branding
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
import requests
import json
import os
import logging
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

from ..client_management.client_crud import ClientCRUD
from ..models.client import Conversation
from ..utils.cache_preloader import get_cache_preloader

# Global database connection - will be set by main.py
admin_db = None

def set_database(database):
    """Set the database connection for widget API"""
    global admin_db
    admin_db = database

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    client_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class MultiTenantChatHandler:
    def __init__(self, database):
        self.db = database
        self.client_crud = ClientCRUD(database)
        self.cache_preloader = get_cache_preloader(database)
        # Force reload of environment variable
        # Use unified domain:port approach for RASA URL
        domain = os.getenv('DOMAIN', 'http://localhost')
        rasa_port = os.getenv('RASA_PORT', '5005')
        self.rasa_url = f"{domain}:{rasa_port}/webhooks/rest/webhook"
    
    async def process_chat_request(self, request: ChatRequest, client_domain: str = None) -> ChatResponse:
        """Process chat request with client context"""
        
        # Processing chat request
        
        # Determine client from request
        client = await self.get_client_context(request.client_id, client_domain)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found or inactive")
        
        # Client found and validated
        
        # Check if client is active (with safe status checking)
        client_status = client.get("status", "pending")  # Default to pending if status not found
        if client_status != "active":
            raise HTTPException(status_code=403, detail="Client account is not active")
        
        # Increment conversation count for billing
        await self.client_crud.increment_conversation_count(client["id"])
        
        # Prepare RASA request with client context
        rasa_request = {
            "sender": f"{client['id']}_{request.session_id}",
            "message": request.message,
            "metadata": {
                "client_id": client["id"],
                "client_config": client["settings"],
                "user_info": request.user_info or {}
            }
        }
        
        # RASA request prepared
        
        # Send to RASA
        try:
            rasa_response = await self.send_to_rasa(rasa_request)
            
            # Process and customize response
            processed_response = await self.process_rasa_response(
                rasa_response, client, request
            )
            
            # Store conversation
            await self.store_conversation(client["id"], request, processed_response)
            
            # Returning successful response
            return ChatResponse(
                response=processed_response,
                session_id=request.session_id,
                client_id=client["id"],
                timestamp=datetime.utcnow(),
                metadata={
                    "client_name": client["business_name"],
                    "response_source": "rasa"
                }
            )
            
        except Exception as e:
            # Fallback response
            fallback_response = self.get_fallback_response(client)
            
            return ChatResponse(
                response=fallback_response,
                session_id=request.session_id,
                client_id=client["id"],
                timestamp=datetime.utcnow(),
                metadata={
                    "client_name": client["business_name"],
                    "response_source": "fallback",
                    "error": str(e)
                }
            )
    
    async def get_client_context(self, client_id: str = None, domain: str = None) -> Optional[Dict[str, Any]]:
        """Get client context from ID or domain with cache optimization"""
        if client_id:
            # Try cache first
            cached_client = self.cache_preloader.get_cached_client_data(client_id)
            if cached_client:
                return cached_client
            # Fallback to database
            return await self.client_crud.get_client(client_id)
        elif domain:
            return await self.client_crud.get_client_by_domain(domain)
        return None
    
    async def send_to_rasa(self, rasa_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send request to RASA with timeout handling"""
        try:
            response = requests.post(
                self.rasa_url,
                json=rasa_request,
                timeout=10
            )
            
            response.raise_for_status()
            response_json = response.json()
            return response_json
        except requests.exceptions.RequestException as e:
            raise Exception(f"RASA request failed: {str(e)}")
    
    async def process_rasa_response(self, rasa_response: List[Dict[str, Any]], 
                                  client: Dict[str, Any], request: ChatRequest) -> str:
        """Process RASA response and apply client customizations"""
        if not rasa_response:
            return self.get_fallback_response(client)
        
        # Combine multiple responses
        combined_response = ""
        for response in rasa_response:
            if "text" in response:
                combined_response += response["text"] + "\n\n"
        
        combined_response = combined_response.strip()
        
        if not combined_response:
            return self.get_fallback_response(client)
        
        # Apply client-specific customizations
        customized_response = await self.apply_client_customizations(
            combined_response, client, request
        )
        
        return customized_response
    
    async def apply_client_customizations(self, response: str, client: Dict[str, Any], 
                                        request: ChatRequest) -> str:
        """Apply client-specific branding and customizations using dynamic information"""
        
        try:
            # Get client-specific information
            from api.utils.information import get_client_support_info
            client_info = get_client_support_info(client["id"])
            company_info = client_info.get_company_info()
            contact_data = client_info.get_all_contact_info()
            
            # Replace placeholder contact information with client-specific data
            if "[PHONE]" in response and contact_data.get("phone_number"):
                response = response.replace("[PHONE]", contact_data["phone_number"])
            
            if "[EMAIL]" in response and contact_data.get("email"):
                response = response.replace("[EMAIL]", contact_data["email"])
            
            if "[ADDRESS]" in response and contact_data.get("address"):
                response = response.replace("[ADDRESS]", contact_data["address"])
            
            if "[COMPANY_NAME]" in response:
                company_name = company_info.get("company_name", client.get("business_name", "our company"))
                response = response.replace("[COMPANY_NAME]", company_name)
            
            if "[WEBSITE]" in response and company_info.get("website"):
                response = response.replace("[WEBSITE]", company_info["website"])
            
            if "[WHATSAPP]" in response and contact_data.get("whatsapp_number"):
                response = response.replace("[WHATSAPP]", contact_data["whatsapp_number"])
            
            # Replace business hours information
            if "[BUSINESS_HOURS]" in response and contact_data.get("support_hours_text"):
                response = response.replace("[BUSINESS_HOURS]", contact_data["support_hours_text"])
            
            # Replace services information
            if "[SERVICES]" in response and company_info.get("services"):
                services_text = ", ".join(company_info["services"])
                response = response.replace("[SERVICES]", services_text)
                
        except Exception as e:
            # Fallback to basic replacements
            if "[COMPANY_NAME]" in response:
                response = response.replace("[COMPANY_NAME]", client.get("business_name", "our company"))
        return response
    
    def get_fallback_response(self, client: Dict[str, Any]) -> str:
        """Get fallback response when RASA is unavailable"""
        company_name = client["business_name"]
        contact_info = client["settings"]["contact_info"]
        
        fallback = f"Hello! I'm the {company_name} automotive assistant. "
        fallback += "I'm experiencing some technical difficulties right now, but I'm here to help! "
        
        if contact_info.get("phone"):
            fallback += f"For immediate assistance, please call us at {contact_info['phone']} "
        
        if contact_info.get("email"):
            fallback += f"or email us at {contact_info['email']}. "
        
        fallback += "Thank you for your patience!"
        
        return fallback
    
    async def store_conversation(self, client_id: str, request: ChatRequest, response: str):
        """Store conversation for analytics and history"""
        try:
            # Validate required fields to prevent E11000 duplicate key errors
            if not client_id or not request.session_id:
                return
                
            # Check if conversation exists
            conversation = await self.db.conversations.find_one({
                "client_id": client_id,
                "session_id": request.session_id
            })
            
            message_data = {
                "role": "user",
                "content": request.message,
                "timestamp": datetime.utcnow()
            }
            
            response_data = {
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.utcnow()
            }
            
            if conversation:
                # Update existing conversation
                await self.db.conversations.update_one(
                    {"_id": conversation["_id"]},
                    {
                        "$push": {
                            "messages": {"$each": [message_data, response_data]}
                        },
                        "$inc": {"total_messages": 2},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
            else:
                # Create new conversation with validated data
                new_conversation = Conversation(
                    client_id=client_id,
                    session_id=request.session_id,
                    user_id=request.user_id or f"anonymous_{request.session_id}",
                    messages=[message_data, response_data],
                    total_messages=2,
                    user_info=request.user_info or {}
                )
                
                # Convert to dict and ensure no None values in required fields
                conversation_dict = new_conversation.dict()
                conversation_dict['created_at'] = datetime.utcnow()
                # Set conversation_id to session_id for backward compatibility
                conversation_dict['conversation_id'] = request.session_id
                
                await self.db.conversations.insert_one(conversation_dict)
                
        except Exception as e:
            # Log error but don't fail the chat request
            pass

# Initialize handler
chat_handler = None

def get_chat_handler(database):
    global chat_handler
    if not chat_handler:
        chat_handler = MultiTenantChatHandler(database)
    return chat_handler

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    client_domain: Optional[str] = Header(None, alias="X-Client-Domain"),
    origin: Optional[str] = Header(None)
):
    """Main chat endpoint for multi-tenant widget"""
    
    # Check if database is available
    if admin_db is None:
        raise HTTPException(
            status_code=503, 
            detail="Database not available. Please try again in a moment."
        )
    
    # Extract domain from origin if not provided
    if not client_domain and origin:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            client_domain = parsed.netloc
        except:
            pass
    
    if not client_domain and not request.client_id:
        raise HTTPException(
            status_code=400, 
            detail="Client domain or client_id required"
        )
    
    handler = get_chat_handler(admin_db)
    return await handler.process_chat_request(request, client_domain)

@router.get("/config/{client_id}")
async def get_widget_config(client_id: str):
    """Get widget configuration for a specific client"""
    
    # Check if database is available
    if admin_db is None:
        raise HTTPException(
            status_code=503, 
            detail="Database not available. Please try again in a moment."
        )
    
    try:
        client_crud = ClientCRUD(admin_db)
        client = await client_crud.get_client(client_id)
        
        if not client or client.get("status") != "active":
            raise HTTPException(status_code=404, detail="Client not found or inactive")
        
        # Get client-specific configurations with error handling
        try:
            branding = await client_crud.get_client_branding(client_id) or {}
        except Exception as e:
            logger.error(f"Error getting branding for client {client_id}: {e}")
            branding = {}
            
        try:
            features = await client_crud.get_client_features(client_id) or {}
        except Exception as e:
            logger.error(f"Error getting features for client {client_id}: {e}")
            features = {}
            
        try:
            contact_info = await client_crud.get_client_contact_info(client_id) or {}
        except Exception as e:
            logger.error(f"Error getting contact info for client {client_id}: {e}")
            contact_info = {}
    
    except Exception as e:
        logger.error(f"Database error in get_widget_config for client {client_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error. Please try again later."
        )
    
    # Use dynamic information system to get client data
    from api.utils.information import get_client_support_info, get_company_info
    
    try:
        client_info = get_client_support_info(client_id)
        company_info = client_info.get_company_info()
        contact_data = client_info.get_all_contact_info()
    except Exception as e:
        logger.warning(f"Could not load client info for {client_id}: {e}")
        # Fallback to basic client data
        company_info = {"company_name": client.get("business_name", "CleverCompanion")}
        contact_data = {}
    
    # Return widget configuration
    return {
        "client_id": client_id,
        "branding": {
            "company_name": company_info.get("company_name", client.get("business_name", "CleverCompanion")),
            "logo_url": branding.get("logo_url", ""),
            "primary_color": branding.get("primary_color", "#3B82F6"),
            "secondary_color": branding.get("secondary_color", "#1E40AF"),
            "welcome_message": branding.get("welcome_message", f"Hello! Welcome to {company_info.get('company_name', 'our automotive service')}. How can I help you today?")
        },
        "features": {
            "menu_enabled": features.get("menu_enabled", True),
            "appointment_booking": features.get("appointment_booking", True),  # Appointment booking feature
            "vehicle_inquiry": features.get("vehicle_search", True),  # Map vehicle_search to vehicle_inquiry
            "test_drive_scheduling": features.get("appointment_booking", True),  # Map appointment_booking to test_drive_scheduling
            "financing_calculator": features.get("loan_calculator", True),  # Map loan_calculator to financing_calculator
            "trade_in_valuation": features.get("trade_in_valuation", True),
            "coe_prices": features.get("coe_prices", True),
            "loan_calculator": features.get("loan_calculator", True),
            "contact_info": features.get("contact_support", True)  # Map contact_support to contact_info
        },
        "contact_info": {
            "phone": contact_data.get("phone_number", contact_info.get("phone", "")),
            "email": contact_data.get("email", contact_info.get("email", "")),
            "whatsapp": contact_data.get("whatsapp_number", contact_info.get("whatsapp", "")),
            "address": contact_data.get("address", contact_info.get("business_address", "")),
            "website": company_info.get("website", "")
        },
        "business_hours": contact_data.get("support_hours", contact_info.get("business_hours", {})),
        "services": company_info.get("services", []),
        "appointment_types": client_info.appointment_types if 'client_info' in locals() else []
    }

@router.get("/embed/{client_id}")
async def generate_embed_code(client_id: str):
    """Generate dynamic embed code for a client"""
    
    # Check if database is available
    if admin_db is None:
        raise HTTPException(
            status_code=503, 
            detail="Database not available. Please try again in a moment."
        )
    
    client_crud = ClientCRUD(admin_db)
    client = await client_crud.get_client(client_id)
    
    if not client or client["status"] != "active":
        raise HTTPException(status_code=404, detail="Client not found or inactive")
    
    # Generate simplified embed JavaScript code
    embed_code = f"""
<!-- CleverCompanion Chatbot Widget -->
<script>
  window.CleverCompanionConfig = {{
    clientId: '{client_id}'
  }};
</script>
<script src="https://your-domain.com/widget/clevercompanion-widget.js" async></script>
<!-- End CleverCompanion Widget -->
"""
    
    return {
        "client_id": client_id,
        "embed_code": embed_code.strip(),
        "instructions": [
            "Copy the simplified embed code above",
            "Paste it before the closing </body> tag on your website",
            "The widget will automatically load your branding and settings from the database",
            "Update your configuration anytime in the dashboard - changes apply instantly",
            "No need to update the embed code when you change settings"
        ]
    }
