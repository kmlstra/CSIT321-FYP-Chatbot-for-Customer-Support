"""Multi-tenant Chat Handler - Minimal implementation for streaming chat compatibility
Main functionality moved to clevercompanion-widget.js as per architecture changes
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import pytz
import logging
import httpx
import asyncio

# Configure logger
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: str
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    timestamp: datetime
    session_id: str
    client_id: str
    metadata: Dict[str, Any] = {}

class ChatHandler:
    """Minimal chat handler for streaming compatibility"""
    
    def __init__(self, db):
        self.db = db
        self.rasa_url = "http://localhost:5005"
    
    async def get_client_context(self, client_id: Optional[str], client_domain: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get client context from database"""
        try:
            if not self.db:
                return None
            
            clients_collection = self.db["clients"]
            client = None
            
            # Try to find by client_id first
            if client_id:
                # Try multiple query patterns to find the client
                try:
                    from bson import ObjectId
                    # Try ObjectId first
                    if ObjectId.is_valid(client_id):
                        client = await clients_collection.find_one({"_id": ObjectId(client_id), "status": "active"})
                except:
                    pass
                
                # If not found, try string _id
                if not client:
                    client = await clients_collection.find_one({"_id": client_id, "status": "active"})
                
                # If still not found, try other fields
                if not client:
                    client = await clients_collection.find_one({
                        "$or": [
                            {"domain": client_id},
                            {"api_key": client_id}
                        ],
                        "status": "active"
                    })
            
            # Try to find by domain if client_id search failed
            if not client and client_domain:
                client = await clients_collection.find_one({
                    "domain": client_domain,
                    "status": "active"
                })
            
            # Convert _id to id for consistency
            if client:
                client["id"] = str(client["_id"])
                # Don't delete _id as it might be needed elsewhere
                return client
            
            # Return default client if no specific client found
            return {
                "id": "default",
                "business_name": "CleverCompanion",
                "domain": client_domain or "localhost",
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error getting client context: {e}")
            return None
    
    async def process_chat_request(self, request: ChatRequest, client_domain: Optional[str] = None) -> ChatResponse:
        """Process chat request through RASA"""
        try:
            # Prepare RASA request
            rasa_payload = {
                "sender": request.session_id,
                "message": request.message,
                "metadata": {
                    "client_id": request.client_id,
                    "user_id": request.user_id,
                    "client_domain": client_domain,
                    "user_info": request.user_info or {}
                }
            }
            
            # Send to RASA
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.rasa_url}/webhooks/rest/webhook",
                    json=rasa_payload
                )
                
                if response.status_code == 200:
                    rasa_responses = response.json()
                    
                    if rasa_responses and len(rasa_responses) > 0:
                        # Process all responses and combine them
                        response_texts = []
                        for rasa_resp in rasa_responses:
                            if rasa_resp.get("text"):
                                response_texts.append(rasa_resp["text"])
                        
                        if response_texts:
                            # Join multiple responses with newlines to preserve multiline format
                            bot_response = "\n".join(response_texts)
                        else:
                            bot_response = "I'm here to help! How can I assist you today?"
                    else:
                        bot_response = "I'm here to help! How can I assist you today?"
                else:
                    logger.error(f"RASA error: {response.status_code} - {response.text}")
                    bot_response = "I'm experiencing technical difficulties. Please try again in a moment."
            
            return ChatResponse(
                response=bot_response,
                timestamp=datetime.now(pytz.timezone('Asia/Singapore')),
                session_id=request.session_id,
                client_id=request.client_id or "default",
                metadata={
                    "response_source": "rasa",
                    "client_domain": client_domain
                }
            )
            
        except asyncio.TimeoutError:
            logger.error("RASA request timeout")
            return ChatResponse(
                response="I apologize for the delay. Please try again in a moment.",
                timestamp=datetime.now(pytz.timezone('Asia/Singapore')),
                session_id=request.session_id,
                client_id=request.client_id or "default",
                metadata={"response_source": "timeout_fallback"}
            )
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            return ChatResponse(
                response="I'm experiencing technical difficulties. Please try again in a moment.",
                timestamp=datetime.now(pytz.timezone('Asia/Singapore')),
                session_id=request.session_id,
                client_id=request.client_id or "default",
                metadata={"response_source": "error_fallback", "error": str(e)}
            )

def get_chat_handler(db) -> ChatHandler:
    """Get chat handler instance"""
    return ChatHandler(db)