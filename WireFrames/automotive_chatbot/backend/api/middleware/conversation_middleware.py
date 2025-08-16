"""Conversation Middleware for RASA Integration
Captures and stores conversation events from RASA.
"""

import json
import logging
import pytz
from typing import Dict, Any, Optional
from datetime import datetime
from ..services.conversation_storage import conversation_storage

logger = logging.getLogger(__name__)
SINGAPORE_TZ = pytz.timezone('Asia/Singapore')

def get_singapore_time():
    """Get current time in Singapore timezone"""
    return datetime.now(SINGAPORE_TZ)

class ConversationTracker:
    """Tracks and stores conversation events."""
    
    @staticmethod
    def get_or_create_session(sender_id: str) -> str:
        """Get existing session or create new one.
        
        Args:
            sender_id: RASA sender identifier
            
        Returns:
            session_id: Session identifier (same as sender_id)
        """
        # Use sender_id directly as session_id to ensure one record per conversation
        logger.debug(f"Using sender_id {sender_id} as session_id")
        return sender_id
    
    @staticmethod
    def store_user_message(sender_id: str, message: str, intent: Optional[str] = None, 
                          entities: Optional[list] = None):
        """Store user message.
        
        Args:
            sender_id: RASA sender identifier
            message: User message text
            intent: Detected intent
            entities: Extracted entities
        """
        session_id = ConversationTracker.get_or_create_session(sender_id)
        
        metadata = {
            'intent': intent,
            'entities': entities or [],
            'confidence': None
        }
        
        conversation_storage.store_message(
            session_id=session_id,
            message_type='user_message',
            content=message,
            sender='user',
            metadata=metadata
        )
        logger.debug(f"User message tracked for {sender_id}: {message[:50]}...")
    
    @staticmethod
    def store_bot_response(sender_id: str, response: str, action_name: Optional[str] = None):
        """Store bot response.
        
        Args:
            sender_id: RASA sender identifier
            response: Bot response text
            action_name: Name of the action that generated the response
        """
        session_id = ConversationTracker.get_or_create_session(sender_id)
        
        metadata = {
            'action_name': action_name,
            'response_type': 'text'
        }
        
        conversation_storage.store_message(
            session_id=session_id,
            message_type='bot_response',
            content=response,
            sender='bot',
            metadata=metadata
        )
        logger.debug(f"Bot response tracked for {sender_id}: {response[:50]}...")
    
    @staticmethod
    def store_action_execution(sender_id: str, action_name: str, success: bool = True, 
                              error_message: Optional[str] = None):
        """Store action execution event.
        
        Args:
            sender_id: RASA sender identifier
            action_name: Name of executed action
            success: Whether action executed successfully
            error_message: Error message if action failed
        """
        session_id = ConversationTracker.get_or_create_session(sender_id)
        
        metadata = {
            'action_name': action_name,
            'success': success,
            'error_message': error_message
        }
        
        content = f"Action executed: {action_name}"
        if not success and error_message:
            content += f" (Error: {error_message})"
        
        conversation_storage.store_message(
            session_id=session_id,
            message_type='action_execution',
            content=content,
            sender='system',
            metadata=metadata
        )
        logger.debug(f"Action execution tracked for {sender_id}: {action_name}")

# ConversationLoggingAction removed - should only be used in RASA actions server
# This middleware is for FastAPI backend integration only

def log_bot_response(sender_id: str, message: str, action_name: Optional[str] = None):
    """Helper function to log bot responses from actions.
    
    Args:
        sender_id: RASA sender identifier
        message: Bot response message
        action_name: Name of the action sending the response
    """
    try:
        ConversationTracker.store_bot_response(
            sender_id=sender_id,
            response=message,
            action_name=action_name
        )
    except Exception as e:
        logger.error(f"Error logging bot response: {e}")

def log_action_execution(sender_id: str, action_name: str, success: bool = True, 
                        error_message: Optional[str] = None):
    """Helper function to log action executions.
    
    Args:
        sender_id: RASA sender identifier
        action_name: Name of executed action
        success: Whether action executed successfully
        error_message: Error message if action failed
    """
    try:
        ConversationTracker.store_action_execution(
            sender_id=sender_id,
            action_name=action_name,
            success=success,
            error_message=error_message
        )
    except Exception as e:
        logger.error(f"Error logging action execution: {e}")

class ConversationAPI:
    """API endpoints for conversation management."""
    
    @staticmethod
    def get_conversation_history(session_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages
            
        Returns:
            Dictionary with conversation data
        """
        try:
            session_info = conversation_storage.get_session_info(session_id)
            messages = conversation_storage.get_conversation_history(session_id, limit)
            
            # Ensure all datetime objects are serialized
            def serialize_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: serialize_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_datetime(item) for item in obj]
                return obj
            
            return {
                'session_id': session_id,
                'session_info': serialize_datetime(session_info),
                'messages': serialize_datetime(messages),
                'message_count': len(messages)
            }
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return {
                'session_id': session_id,
                'session_info': None,
                'messages': [],
                'message_count': 0,
                'error': str(e)
            }
    
    @staticmethod
    def get_active_sessions() -> Dict[str, Any]:
        """Get information about active sessions.
        
        Returns:
            Dictionary with active session data
        """
        try:
            active_count = conversation_storage.get_active_sessions_count()
            return {
                'active_sessions': active_count,
                'timestamp': get_singapore_time().isoformat()
            }
        except Exception as e:
            logger.error(f"Error retrieving active sessions: {e}")
            return {
                'active_sessions': 0,
                'timestamp': get_singapore_time().isoformat(),
                'error': str(e)
            }
    
    @staticmethod
    def cleanup_expired_sessions() -> Dict[str, Any]:
        """Clean up expired sessions.
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            cleaned_count = conversation_storage.cleanup_expired_sessions()
            return {
                'cleaned_sessions': cleaned_count,
                'timestamp': get_singapore_time().isoformat()
            }
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return {
                'cleaned_sessions': 0,
                'timestamp': get_singapore_time().isoformat(),
                'error': str(e)
            }