"""Streaming Chat API - Provides immediate acknowledgments and typing indicators
Implements response streaming for better perceived performance
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)

from .multi_tenant_chat import get_chat_handler, ChatRequest, admin_db

router = APIRouter()

class StreamingChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None

class AckResponse(BaseModel):
    type: str = "acknowledgment"
    message: str = "Message received, processing..."
    timestamp: datetime
    session_id: str
    client_id: str

class TypingResponse(BaseModel):
    type: str = "typing"
    message: str = "Bot is typing..."
    timestamp: datetime
    session_id: str
    client_id: str

class FinalResponse(BaseModel):
    type: str = "response"
    response: str
    timestamp: datetime
    session_id: str
    client_id: str
    metadata: Dict[str, Any] = {}

@router.post("/chat/stream")
async def streaming_chat_endpoint(
    request: StreamingChatRequest,
    client_domain: Optional[str] = Header(None, alias="X-Client-Domain"),
    origin: Optional[str] = Header(None)
):
    """Streaming chat endpoint with immediate acknowledgment and typing indicators"""
    
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
    
    async def generate_streaming_response():
        """Generate streaming response with immediate acknowledgment"""
        try:
            # Get chat handler
            handler = get_chat_handler(admin_db)
            
            # Determine client context first for immediate acknowledgment
            client = await handler.get_client_context(request.client_id, client_domain)
            if not client:
                error_response = {
                    "type": "error",
                    "message": "Client not found or inactive",
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": request.session_id,
                    "client_id": request.client_id or "unknown"
                }
                yield f"data: {json.dumps(error_response)}\n\n"
                return
            
            client_id = client["id"]
            company_name = client.get("business_name", "our team")
            
            # 1. Send immediate acknowledgment
            ack_response = AckResponse(
                message=f"Thanks for your message! {company_name} is processing your request...",
                timestamp=datetime.utcnow(),
                session_id=request.session_id,
                client_id=client_id
            )
            yield f"data: {ack_response.json()}\n\n"
            
            # 2. Brief delay then send typing indicator
            await asyncio.sleep(0.5)
            typing_response = TypingResponse(
                message=f"{company_name} assistant is typing...",
                timestamp=datetime.utcnow(),
                session_id=request.session_id,
                client_id=client_id
            )
            yield f"data: {typing_response.json()}\n\n"
            
            # 3. Process the actual chat request
            chat_request = ChatRequest(
                message=request.message,
                session_id=request.session_id,
                user_id=request.user_id,
                client_id=client_id,
                user_info=request.user_info
            )
            
            # Process chat with timeout handling
            try:
                chat_response = await asyncio.wait_for(
                    handler.process_chat_request(chat_request, client_domain),
                    timeout=15.0  # 15 second timeout
                )
                
                # 4. Send final response
                final_response = FinalResponse(
                    response=chat_response.response,
                    timestamp=chat_response.timestamp,
                    session_id=chat_response.session_id,
                    client_id=chat_response.client_id,
                    metadata=chat_response.metadata
                )
                yield f"data: {final_response.json()}\n\n"
                
            except asyncio.TimeoutError:
                # Send timeout fallback response
                fallback_response = FinalResponse(
                    response=f"I apologize for the delay. {company_name} is experiencing high demand right now. Please try again in a moment, or contact us directly for immediate assistance.",
                    timestamp=datetime.utcnow(),
                    session_id=request.session_id,
                    client_id=client_id,
                    metadata={"response_source": "timeout_fallback"}
                )
                yield f"data: {fallback_response.json()}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming chat: {e}")
                # Send error fallback response
                error_fallback = FinalResponse(
                    response=f"I'm experiencing technical difficulties right now. Please try again in a moment or contact {company_name} directly for assistance.",
                    timestamp=datetime.utcnow(),
                    session_id=request.session_id,
                    client_id=client_id,
                    metadata={"response_source": "error_fallback", "error": str(e)}
                )
                yield f"data: {error_fallback.json()}\n\n"
            
            # 5. Send completion signal
            completion_signal = {
                "type": "complete",
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": request.session_id,
                "client_id": client_id
            }
            yield f"data: {completion_signal}\n\n"
            
        except Exception as e:
            logger.error(f"Critical error in streaming response: {e}")
            error_response = {
                "type": "error",
                "message": "A critical error occurred. Please refresh and try again.",
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": request.session_id,
                "client_id": request.client_id or "unknown"
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.post("/chat/quick-ack")
async def quick_acknowledgment(
    request: StreamingChatRequest,
    client_domain: Optional[str] = Header(None, alias="X-Client-Domain"),
    origin: Optional[str] = Header(None)
):
    """Provide immediate acknowledgment for chat messages"""
    
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
    
    try:
        # Get client context for personalized acknowledgment
        handler = get_chat_handler(admin_db)
        client = await handler.get_client_context(request.client_id, client_domain)
        
        if not client:
            company_name = "our team"
            client_id = request.client_id or "unknown"
        else:
            company_name = client.get("business_name", "our team")
            client_id = client["id"]
        
        # Return immediate acknowledgment
        return AckResponse(
            message=f"Message received! {company_name} is processing your request...",
            timestamp=datetime.utcnow(),
            session_id=request.session_id,
            client_id=client_id
        )
        
    except Exception as e:
        logger.error(f"Error in quick acknowledgment: {e}")
        return AckResponse(
            message="Message received! Processing your request...",
            timestamp=datetime.utcnow(),
            session_id=request.session_id,
            client_id=request.client_id or "unknown"
        )