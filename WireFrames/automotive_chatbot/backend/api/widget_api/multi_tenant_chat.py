"""
Multi-tenant Chat API - Routes chat requests to correct client context
Handles widget chat requests with client-specific data and branding
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
import requests
import json
from datetime import datetime

from ..client_management.client_crud import ClientCRUD
from ..models.client import Conversation

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
        self.rasa_url = "http://localhost:5005/webhooks/rest/webhook"
    
    async def process_chat_request(self, request: ChatRequest, client_domain: str = None) -> ChatResponse:
        """Process chat request with client context"""
        
        # Determine client from request
        client = await self.get_client_context(request.client_id, client_domain)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found or inactive")
        
        # Check if client is active
        if client["status"] != "active":
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
        
        # Send to RASA
        try:
            rasa_response = await self.send_to_rasa(rasa_request)
            
            # Process and customize response
            processed_response = await self.process_rasa_response(
                rasa_response, client, request
            )
            
            # Store conversation
            await self.store_conversation(client["id"], request, processed_response)
            
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
        """Get client context from ID or domain"""
        if client_id:
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
            return response.json()
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
        
        # Apply client-specific customizations
        customized_response = await self.apply_client_customizations(
            combined_response.strip(), client, request
        )
        
        return customized_response
    
    async def apply_client_customizations(self, response: str, client: Dict[str, Any], 
                                        request: ChatRequest) -> str:
        """Apply client-specific branding and customizations"""
        
        # Replace generic contact info with client-specific info
        contact_info = client["settings"]["contact_info"]
        
        # Replace placeholder contact information
        if "[PHONE]" in response and contact_info.get("phone"):
            response = response.replace("[PHONE]", contact_info["phone"])
        
        if "[EMAIL]" in response and contact_info.get("email"):
            response = response.replace("[EMAIL]", contact_info["email"])
        
        if "[ADDRESS]" in response and contact_info.get("address"):
            response = response.replace("[ADDRESS]", contact_info["address"])
        
        if "[COMPANY_NAME]" in response:
            response = response.replace("[COMPANY_NAME]", client["business_name"])
        
        # Apply custom responses if configured
        custom_responses = client["settings"].get("custom_responses", {})
        for trigger, custom_response in custom_responses.items():
            if trigger.lower() in request.message.lower():
                response = custom_response
                break
        
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
                # Create new conversation
                new_conversation = Conversation(
                    client_id=client_id,
                    session_id=request.session_id,
                    user_id=request.user_id or f"anonymous_{request.session_id}",
                    messages=[message_data, response_data],
                    total_messages=2,
                    user_info=request.user_info
                )
                
                await self.db.conversations.insert_one(new_conversation.dict())
                
        except Exception as e:
            # Log error but don't fail the chat request
            print(f"Failed to store conversation: {str(e)}")

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
    origin: Optional[str] = Header(None),
    database = None  # Will be injected by dependency
):
    """Main chat endpoint for multi-tenant widget"""
    
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
    
    handler = get_chat_handler(database)
    return await handler.process_chat_request(request, client_domain)

@router.get("/config/{client_id}")
async def get_widget_config(client_id: str, database = None):
    """Get widget configuration for a specific client"""
    
    client_crud = ClientCRUD(database)
    client = await client_crud.get_client(client_id)
    
    if not client or client["status"] != "active":
        raise HTTPException(status_code=404, detail="Client not found or inactive")
    
    # Return widget configuration
    return {
        "client_id": client["id"],
        "branding": client["settings"]["branding"],
        "features": client["settings"]["features"],
        "contact_info": client["settings"]["contact_info"],
        "business_hours": client["settings"]["business_hours"],
        "welcome_message": client["settings"].get("custom_welcome_message", 
                                                 f"Hello! Welcome to {client['business_name']}. How can I help you today?")
    }

@router.get("/embed/{client_id}")
async def generate_embed_code(client_id: str, database = None):
    """Generate dynamic embed code for a client"""
    
    client_crud = ClientCRUD(database)
    client = await client_crud.get_client(client_id)
    
    if not client or client["status"] != "active":
        raise HTTPException(status_code=404, detail="Client not found or inactive")
    
    # Generate embed JavaScript code
    embed_code = f"""
<!-- CleverCompanion Automotive Chatbot Widget -->
<script>
  window.CleverCompanionConfig = {{
    clientId: '{client_id}',
    apiUrl: 'https://your-domain.com/api/widget',
    branding: {json.dumps(client["settings"]["branding"])},
    features: {json.dumps(client["settings"]["features"])}
  }};
</script>
<script src="https://your-domain.com/widget/clevercompanion-widget.js" async></script>
<!-- End CleverCompanion Widget -->
"""
    
    return {
        "client_id": client_id,
        "embed_code": embed_code.strip(),
        "instructions": [
            "Copy the embed code above",
            "Paste it before the closing </body> tag on your website",
            "The chatbot will automatically appear on your site",
            "Customize appearance in your dashboard"
        ]
    }