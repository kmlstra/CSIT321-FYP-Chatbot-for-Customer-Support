"""RASA Proxy Router
Proxies requests to RASA and captures conversation data.
"""

import json
import logging
import httpx
import asyncio
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
        logger.debug(f"User message stored asynchronously for session {session_id}")
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
        logger.debug(f"Bot message stored asynchronously for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to store bot message asynchronously: {e}")

@router.post("/chat")
async def chat_with_rasa(chat_request: ChatMessage, background_tasks: BackgroundTasks):
    """Proxy chat requests to RASA and capture conversation data."""
    
    try:
        sender_id = chat_request.sender
        user_message = chat_request.message
        
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
        
        # Retry logic for RASA connection
        max_retries = 3
        retry_delay = 1.0  # seconds
        rasa_responses = None
        
        for attempt in range(max_retries):
            try:
<<<<<<< Updated upstream
                response = await client.post(
                    "http://localhost:5005/webhooks/rest/webhook",
                    json=rasa_payload,
                    timeout=10.0  # Reduced from 30s to 10s for faster response
                )
                response.raise_for_status()
                rasa_responses = response.json()
=======
                async with httpx.AsyncClient() as client:
                    domain = os.getenv('DOMAIN', 'http://localhost')
                    rasa_port = os.getenv('RASA_PORT', '5005')
                    rasa_url = f"{domain}:{rasa_port}/webhooks/rest/webhook"
                    
                    logger.info(f"Attempting RASA connection (attempt {attempt + 1}/{max_retries})")
                    response = await client.post(
                        rasa_url,
                        json=rasa_payload,
                        timeout=30.0  # Increased to 30s to prevent timeout errors
                    )
                    response.raise_for_status()
                    rasa_responses = response.json()
                    logger.info(f"RASA connection successful on attempt {attempt + 1}")
                    break  # Success, exit retry loop
                    
            except (httpx.RequestError, httpx.HTTPStatusError, httpx.ReadTimeout) as e:
                logger.warning(f"RASA connection attempt {attempt + 1} failed: {e}")
>>>>>>> Stashed changes
                
                if attempt == max_retries - 1:  # Last attempt failed
                    logger.error(f"All RASA connection attempts failed. Providing fallback response.")
                    # Provide fallback response instead of crashing
                    fallback_response = {
                        'text': "I'm sorry, I'm having trouble connecting to our chat service right now. Please try again in a moment, or contact our support team for immediate assistance.",
                        'buttons': []
                    }
                    
                    # Store fallback response
                    bot_metadata = {
                        'timestamp': datetime.now(pytz.timezone('Asia/Singapore')).isoformat(),
                        'source': 'fallback_response',
                        'reason': 'rasa_connection_failed',
                        'has_buttons': False
                    }
                    background_tasks.add_task(store_bot_message_async, sender_id, fallback_response['text'], bot_metadata)
                    
                    return JSONResponse(content={
                        "success": True,
                        "sender": sender_id,
                        "user_message": user_message,
                        "bot_responses": [fallback_response],
                        "fallback": True,
                        "error": "RASA service temporarily unavailable"
                    })
                else:
                    # Wait before retrying
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        # FIX 2: Process bot responses and store asynchronously (non-blocking)
        bot_messages = []
        if isinstance(rasa_responses, list):
            for bot_response in rasa_responses:
                bot_text = bot_response.get('text', '')
                bot_buttons = bot_response.get('buttons', [])
                
                # Create message object with text and buttons
                message_obj = {
                    'text': bot_text,
                    'buttons': bot_buttons
                }
                
                # Only add to bot_messages if there's text or buttons
                if bot_text or bot_buttons:
                    bot_messages.append(message_obj)
                    logger.info(f"Bot response for {sender_id}: text='{bot_text[:50]}...', buttons={len(bot_buttons)}")
                    
                    # Store bot response asynchronously in background
                    bot_metadata = {
                        'timestamp': datetime.now(pytz.timezone('Asia/Singapore')).isoformat(),
                        'source': 'rasa_response',
                        'action_name': bot_response.get('custom', {}).get('action_name'),
                        'has_buttons': len(bot_buttons) > 0
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
    """Check RASA service status with improved timeout and error handling."""
    try:
        async with httpx.AsyncClient() as client:
<<<<<<< Updated upstream
            response = await client.get(
                "http://localhost:5005/status",
                timeout=5.0
=======
            domain = os.getenv('DOMAIN', 'http://localhost')
            rasa_port = os.getenv('RASA_PORT', '5005')
            rasa_status_url = f"{domain}:{rasa_port}/status"
            
            logger.info("Checking RASA service status")
            response = await client.get(
                rasa_status_url,
                timeout=30.0  # Increased timeout to match chat endpoint
>>>>>>> Stashed changes
            )
            response.raise_for_status()
            logger.info("RASA service status check successful")
            return JSONResponse(content={
                "rasa_status": "available",
                "rasa_response": response.json()
            })
    except (httpx.RequestError, httpx.HTTPStatusError, httpx.ReadTimeout) as e:
        logger.warning(f"RASA status check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "rasa_status": "unavailable",
                "error": str(e),
                "message": "RASA service is temporarily unavailable"
            }
        )