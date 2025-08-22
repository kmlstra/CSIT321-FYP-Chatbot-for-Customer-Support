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

# Import unified conversation service
try:
    from api.services.conversation_service import UnifiedConversationService, MessageType
    unified_conversation_service = UnifiedConversationService()
    print("UnifiedConversationService imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
    # Try alternative import path
    try:
        from services.conversation_service import UnifiedConversationService, MessageType
        unified_conversation_service = UnifiedConversationService()
        print("UnifiedConversationService imported successfully (alternative path)")
    except ImportError as e2:
        print(f"Alternative import also failed: {e2}")
        # Fallback if import fails
        class MockUnifiedConversationService:
            def store_message(self, **kwargs):
                print(f"Mock unified storage: {kwargs}")
                return True
        
        unified_conversation_service = MockUnifiedConversationService()
        print("Using MockUnifiedConversationService as fallback")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rasa", tags=["rasa-proxy"])

class ChatMessage(BaseModel):
    sender: str
    message: str
    metadata: Dict[str, Any] = {}

# Background task functions for async database storage
async def store_user_message_async(session_id: str, content: str, metadata: Dict[str, Any]):
    """Store user message asynchronously in background using unified conversation service."""
    try:
        # Extract client_id from metadata
        client_id = metadata.get('client_id', 'unknown')
        
        # Store message using unified conversation service
        success = unified_conversation_service.store_message(
            session_id=session_id,
            message=content,
            message_type=MessageType.USER,
            metadata=metadata,
            client_id=client_id
        )
        
        if not success:
            logger.error(f"Failed to store user message for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to store user message asynchronously: {e}")

async def store_bot_message_async(session_id: str, content: str, metadata: Dict[str, Any]):
    """Store bot message asynchronously in background using unified conversation service."""
    try:
        # Extract client_id from metadata
        client_id = metadata.get('client_id', 'unknown')
        
        # Store message using unified conversation service
        success = unified_conversation_service.store_message(
            session_id=session_id,
            message=content,
            message_type=MessageType.ASSISTANT,
            metadata=metadata,
            client_id=client_id
        )
        
        if not success:
            logger.error(f"Failed to store bot message for session {session_id}")
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
        
        # CRITICAL FIX: Use sender_id directly as session_id for conversation storage
        # This ensures consistency with the composite format used in multi_tenant_chat.py
        # The sender_id from multi_tenant_chat.py is already in format: {client_id}_{session_id}
        session_id = sender_id
        logger.info(f"Using session_id for conversation storage: {session_id}")
        
        logger.info(f"Chat request from {sender_id}: {user_message}")
        
        # Extract client_id from request metadata for proper conversation tagging
        client_id = None
        if chat_request.metadata:
            client_id = chat_request.metadata.get('client_id') or chat_request.metadata.get('clientId')
            # Also check for client_id in nested metadata
            if not client_id and 'metadata' in chat_request.metadata:
                nested_metadata = chat_request.metadata['metadata']
                if isinstance(nested_metadata, dict):
                    client_id = nested_metadata.get('client_id') or nested_metadata.get('clientId')
        
        # FIX 2: Store user message asynchronously in background (non-blocking)
        user_metadata = {
            'timestamp': datetime.now(pytz.timezone('Asia/Singapore')).isoformat(),
            'source': 'api_proxy',
            **chat_request.metadata
        }
        
        # Ensure client_id is included in metadata for conversation storage
        if client_id:
            user_metadata['client_id'] = client_id
            
        background_tasks.add_task(store_user_message_async, session_id, user_message, user_metadata)
        
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
                async with httpx.AsyncClient() as client:
                    # Check if running in Docker container
                    import socket
                    try:
                        # Try to resolve 'rasa' hostname (Docker container name)
                        socket.gethostbyname('rasa')
                        # If successful, we're in Docker environment
                        rasa_url = "http://rasa:5005/webhooks/rest/webhook"
                        logger.info("Using Docker container name for RASA connection")
                    except socket.gaierror:
                        # Not in Docker, use external domain
                        domain = os.getenv('DOMAIN', 'http://localhost')
                        rasa_port = os.getenv('RASA_PORT', '5005')
                        rasa_url = f"{domain}:{rasa_port}/webhooks/rest/webhook"
                        logger.info("Using external domain for RASA connection")
                    
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
                
                if attempt == max_retries - 1:  # Last attempt failed
                    logger.error(f"All RASA connection attempts failed. Checking Actions service and providing fallback response.")
                    
                    # Check if Actions service is available for enhanced fallback
                    actions_available = False
                    try:
                        async with httpx.AsyncClient() as actions_client:
                            # Check if running in Docker container for Actions service
                            import socket
                            try:
                                socket.gethostbyname('rasa-actions')
                                actions_url = "http://rasa-actions:5055/health"
                            except socket.gaierror:
                                domain = os.getenv('DOMAIN', 'http://localhost')
                                rasa_actions_port = os.getenv('RASA_ACTIONS_PORT', '5055')
                                actions_url = f"{domain}:{rasa_actions_port}/health"
                            
                            actions_response = await actions_client.get(actions_url, timeout=10.0)
                            actions_response.raise_for_status()
                            actions_available = True
                            logger.info("RASA Actions service is available despite core service failure")
                    except Exception as actions_e:
                        logger.warning(f"RASA Actions service also unavailable: {actions_e}")
                    
                    # Provide enhanced fallback response based on service availability
                    if actions_available:
                        fallback_response = {
                            'text': "I'm experiencing some technical difficulties with my main chat service, but my action handlers are still working. Please try a simple question or contact our support team for immediate assistance.",
                            'buttons': [
                                {'title': 'Contact Support', 'payload': '/contact_support'},
                                {'title': 'Try Again', 'payload': '/restart'}
                            ]
                        }
                        fallback_reason = 'rasa_core_failed_actions_available'
                    else:
                        fallback_response = {
                            'text': "I'm sorry, I'm having trouble connecting to our chat service right now. Please try again in a moment, or contact our support team for immediate assistance.",
                            'buttons': [
                                {'title': 'Contact Support', 'payload': '/contact_support'},
                                {'title': 'Retry', 'payload': '/restart'}
                            ]
                        }
                        fallback_reason = 'all_rasa_services_failed'
                    
                    # Store fallback response
                    bot_metadata = {
                        'timestamp': datetime.now(pytz.timezone('Asia/Singapore')).isoformat(),
                        'source': 'enhanced_fallback_response',
                        'reason': fallback_reason,
                        'has_buttons': len(fallback_response['buttons']) > 0,
                        'actions_service_status': 'available' if actions_available else 'unavailable'
                    }
                    
                    # Include client_id in fallback response metadata
                    if client_id:
                        bot_metadata['client_id'] = client_id
                        
                    background_tasks.add_task(store_bot_message_async, session_id, fallback_response['text'], bot_metadata)
                    
                    return JSONResponse(content={
                        "success": True,
                        "sender": sender_id,
                        "user_message": user_message,
                        "bot_responses": [fallback_response],
                        "fallback": True,
                        "error": "RASA service temporarily unavailable",
                        "service_status": {
                            "rasa_core": "unavailable",
                            "rasa_actions": "available" if actions_available else "unavailable"
                        }
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
                    
                    # Include client_id in bot response metadata
                    if client_id:
                        bot_metadata['client_id'] = client_id
                        
                    background_tasks.add_task(store_bot_message_async, session_id, bot_text, bot_metadata)
        
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
            # Check if running in Docker container
            import socket
            try:
                # Try to resolve 'rasa' hostname (Docker container name)
                socket.gethostbyname('rasa')
                # If successful, we're in Docker environment
                rasa_status_url = "http://rasa:5005/status"
                logger.info("Using Docker container name for RASA status check")
            except socket.gaierror:
                # Not in Docker, use external domain
                domain = os.getenv('DOMAIN', 'http://localhost')
                rasa_port = os.getenv('RASA_PORT', '5005')
                rasa_status_url = f"{domain}:{rasa_port}/status"
                logger.info("Using external domain for RASA status check")
            
            logger.info("Checking RASA service status")
            response = await client.get(
                rasa_status_url,
                timeout=30.0  # Increased timeout to match chat endpoint
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

@router.get("/actions/status")
async def rasa_actions_status():
    """Check RASA Actions service status (port 5055) with improved timeout and error handling."""
    try:
        async with httpx.AsyncClient() as client:
            # Check if running in Docker container
            import socket
            try:
                # Try to resolve 'rasa-actions' hostname (Docker container name)
                socket.gethostbyname('rasa-actions')
                # If successful, we're in Docker environment
                rasa_actions_status_url = "http://rasa-actions:5055/health"
                logger.info("Using Docker container name for RASA Actions status check")
            except socket.gaierror:
                # Not in Docker, use external domain
                domain = os.getenv('DOMAIN', 'http://localhost')
                rasa_actions_port = os.getenv('RASA_ACTIONS_PORT', '5055')
                rasa_actions_status_url = f"{domain}:{rasa_actions_port}/health"
                logger.info("Using external domain for RASA Actions status check")
            
            logger.info("Checking RASA Actions service status")
            response = await client.get(
                rasa_actions_status_url,
                timeout=30.0
            )
            response.raise_for_status()
            logger.info("RASA Actions service status check successful")
            return JSONResponse(content={
                "rasa_actions_status": "available",
                "rasa_actions_response": response.json() if response.content else {"status": "healthy"}
            })
    except (httpx.RequestError, httpx.HTTPStatusError, httpx.ReadTimeout) as e:
        logger.warning(f"RASA Actions status check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "rasa_actions_status": "unavailable",
                "error": str(e),
                "message": "RASA Actions service is temporarily unavailable"
            }
        )

@router.get("/health")
async def combined_health_check():
    """Combined health check for both RASA core (5005) and Actions (5055) services."""
    try:
        async with httpx.AsyncClient() as client:
            # Check if running in Docker container
            import socket
            docker_mode = False
            try:
                socket.gethostbyname('rasa')
                docker_mode = True
                logger.info("Running in Docker environment")
            except socket.gaierror:
                logger.info("Running in external environment")
            
            # Prepare URLs based on environment
            if docker_mode:
                rasa_status_url = "http://rasa:5005/status"
                rasa_actions_status_url = "http://rasa-actions:5055/health"
            else:
                domain = os.getenv('DOMAIN', 'http://localhost')
                rasa_port = os.getenv('RASA_PORT', '5005')
                rasa_actions_port = os.getenv('RASA_ACTIONS_PORT', '5055')
                rasa_status_url = f"{domain}:{rasa_port}/status"
                rasa_actions_status_url = f"{domain}:{rasa_actions_port}/health"
            
            # Check both services concurrently
            results = {
                "rasa_core": {"status": "unknown", "error": None},
                "rasa_actions": {"status": "unknown", "error": None},
                "overall_status": "unknown"
            }
            
            # Check RASA Core (5005)
            try:
                logger.info("Checking RASA Core service")
                rasa_response = await client.get(rasa_status_url, timeout=15.0)
                rasa_response.raise_for_status()
                results["rasa_core"]["status"] = "available"
                results["rasa_core"]["response"] = rasa_response.json()
                logger.info("RASA Core service is available")
            except Exception as e:
                results["rasa_core"]["status"] = "unavailable"
                results["rasa_core"]["error"] = str(e)
                logger.warning(f"RASA Core service check failed: {e}")
            
            # Check RASA Actions (5055)
            try:
                logger.info("Checking RASA Actions service")
                actions_response = await client.get(rasa_actions_status_url, timeout=15.0)
                actions_response.raise_for_status()
                results["rasa_actions"]["status"] = "available"
                results["rasa_actions"]["response"] = actions_response.json() if actions_response.content else {"status": "healthy"}
                logger.info("RASA Actions service is available")
            except Exception as e:
                results["rasa_actions"]["status"] = "unavailable"
                results["rasa_actions"]["error"] = str(e)
                logger.warning(f"RASA Actions service check failed: {e}")
            
            # Determine overall status
            if results["rasa_core"]["status"] == "available" and results["rasa_actions"]["status"] == "available":
                results["overall_status"] = "healthy"
                status_code = 200
            elif results["rasa_core"]["status"] == "available" or results["rasa_actions"]["status"] == "available":
                results["overall_status"] = "partial"
                status_code = 206  # Partial Content
            else:
                results["overall_status"] = "unhealthy"
                status_code = 503  # Service Unavailable
            
            return JSONResponse(
                status_code=status_code,
                content=results
            )
            
    except Exception as e:
        logger.error(f"Combined health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "overall_status": "error",
                "error": str(e),
                "message": "Health check system error"
            }
        )