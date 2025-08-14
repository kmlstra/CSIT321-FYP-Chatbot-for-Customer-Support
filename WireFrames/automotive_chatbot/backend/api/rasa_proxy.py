"""RASA Proxy Router
Proxies requests to RASA and captures conversation data.
"""

import json
import logging
import httpx
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pytz

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from api.services.conversation_storage import ConversationStorage
    conversation_storage = ConversationStorage()
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback if import fails
    class MockConversationStorage:
        def store_message(self, **kwargs):
            print(f"Mock storage: {kwargs}")
    
    conversation_storage = MockConversationStorage()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rasa", tags=["rasa-proxy"])

class ChatMessage(BaseModel):
    sender: str
    message: str
    metadata: Dict[str, Any] = {}

# Background task functions for async database storage
async def store_user_message_async(session_id: str, content: str, metadata: Dict[str, Any]):
    """Store user message asynchronously in background."""
    try:
        conversation_storage.store_message(
            session_id=session_id,
            message_type='user_message',
            content=content,
            sender='user',
            metadata=metadata
        )
        pass
    except Exception as e:
        logger.error(f"Failed to store user message asynchronously: {e}")

async def store_bot_message_async(session_id: str, content: str, metadata: Dict[str, Any]):
    """Store bot message asynchronously in background."""
    try:
        conversation_storage.store_message(
            session_id=session_id,
            message_type='bot_response',
            content=content,
            sender='bot',
            metadata=metadata
        )
        pass
    except Exception as e:
        logger.error(f"Failed to store bot message asynchronously: {e}")

@router.post("/chat")
async def chat_with_rasa(chat_request: ChatMessage, background_tasks: BackgroundTasks):
    """Proxy chat requests to RASA and capture conversation data."""
    
    try:
        sender_id = chat_request.sender
        user_message = chat_request.message
        
        # FIX: Validate sender_id to prevent null conversation_id errors
        if not sender_id or sender_id.strip() == '' or sender_id == 'null':
            # Generate a fallback session ID if sender_id is invalid
            sender_id = f"fallback_session_{datetime.now().timestamp()}_{hash(user_message) % 10000}"
            logger.warning(f"Invalid sender_id received, using fallback: {sender_id}")
        
        logger.info(f"Chat request from {sender_id}: {user_message}")
        
        # FIX 2: Store user message asynchronously in background (non-blocking)
        user_metadata = {
            'timestamp': datetime.now(pytz.timezone('Asia/Singapore')).isoformat(),
            'source': 'api_proxy',
            **chat_request.metadata
        }
        background_tasks.add_task(store_user_message_async, sender_id, user_message, user_metadata)
        
        # Forward request to RASA
        rasa_payload = {
            "sender": sender_id,
            "message": user_message
        }
        
        async with httpx.AsyncClient() as client:
            try:
                domain = os.getenv('DOMAIN', 'http://localhost')
                rasa_port = os.getenv('RASA_PORT', '5005')
                rasa_url = f"{domain}:{rasa_port}/webhooks/rest/webhook"
                response = await client.post(
                    rasa_url,
                    json=rasa_payload,
                    timeout=3.0  # Reduced to 3s for faster response
                )
                response.raise_for_status()
                rasa_responses = response.json()
                
            except httpx.RequestError as e:
                logger.error(f"Error connecting to RASA: {e}")
                raise HTTPException(status_code=503, detail="RASA service unavailable")
            except httpx.HTTPStatusError as e:
                logger.error(f"RASA returned error: {e}")
                raise HTTPException(status_code=502, detail="RASA service error")
        
        # FIX 2: Process bot responses and store asynchronously (non-blocking)
        bot_messages = []
        if isinstance(rasa_responses, list):
            for bot_response in rasa_responses:
                bot_text = bot_response.get('text', '')
                if bot_text:
                    bot_messages.append(bot_text)
                    logger.info(f"Bot response for {sender_id}: {bot_text[:50]}...")
                    
                    # Store bot response asynchronously in background
                    bot_metadata = {
                        'timestamp': datetime.now(pytz.timezone('Asia/Singapore')).isoformat(),
                        'source': 'rasa_response',
                        'action_name': bot_response.get('custom', {}).get('action_name')
                    }
                    background_tasks.add_task(store_bot_message_async, sender_id, bot_text, bot_metadata)
        
        return JSONResponse(content={
            "success": True,
            "sender": sender_id,
            "user_message": user_message,
            "bot_responses": bot_messages,
            "raw_rasa_response": rasa_responses
        })
        
    except Exception as e:
        logger.error(f"Error in chat proxy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status")
async def rasa_status():
    """Check RASA service status."""
    try:
        async with httpx.AsyncClient() as client:
            domain = os.getenv('DOMAIN', 'http://localhost')
            rasa_port = os.getenv('RASA_PORT', '5005')
            rasa_status_url = f"{domain}:{rasa_port}/status"
            response = await client.get(
                rasa_status_url,
                timeout=3.0
            )
            response.raise_for_status()
            return JSONResponse(content={
                "rasa_status": "available",
                "rasa_response": response.json()
            })
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "rasa_status": "unavailable",
                "error": str(e)
            }
        )