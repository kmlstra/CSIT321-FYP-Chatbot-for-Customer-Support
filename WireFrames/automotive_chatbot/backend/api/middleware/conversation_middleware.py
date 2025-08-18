"""Conversation Middleware for RASA Integration
Captures and stores conversation events from RASA.
"""

import json
import logging
import pytz
from typing import Dict, Any, Optional
from datetime import datetime
from api.services.conversation_service import unified_conversation_service, MessageType
from api.services.unified_session_manager import unified_session_manager
from api.utils.timezone_utils import get_singapore_time

logger = logging.getLogger(__name__)
SINGAPORE_TZ = pytz.timezone('Asia/Singapore')

# Initialize unified conversation service
try:
    # unified_conversation_service is already initialized in conversation_service.py
    pass
except Exception as e:
    logger.error(f"Failed to initialize UnifiedConversationService: {e}")
    # Create a mock service for fallback
    class MockUnifiedConversationService:
        def store_message(self, *args, **kwargs):
            logger.warning("Mock service: message not stored")
            return True
        def get_conversation_history(self, *args, **kwargs):
            return []
        def get_conversation_summary(self, *args, **kwargs):
            return {'total_messages': 0, 'participants': []}
        def archive_conversation(self, *args, **kwargs):
            return True
    
    unified_conversation_service = MockUnifiedConversationService()

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
        """Store user message with intent and entities.
        
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
            'confidence': None,
            'client_id': sender_id  # Use sender_id as client_id for compatibility
        }
        
        try:
            unified_conversation_service.store_message(
                session_id=session_id,
                message_type=MessageType.USER,
                message=message,
                client_id=sender_id,
                metadata=metadata
            )
            logger.debug(f"User message tracked for {sender_id}: {message[:50]}...")
        except Exception as e:
            logger.error(f"Failed to store user message for {sender_id}: {e}")
    
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
            'response_type': 'text',
            'client_id': sender_id  # Use sender_id as client_id for compatibility
        }
        
        try:
            unified_conversation_service.store_message(
                session_id=session_id,
                message_type=MessageType.ASSISTANT,
                message=response,
                client_id=sender_id,
                metadata=metadata
            )
            logger.debug(f"Bot response tracked for {sender_id}: {response[:50]}...")
        except Exception as e:
            logger.error(f"Failed to store bot response for {sender_id}: {e}")
    
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
            'error_message': error_message,
            'client_id': sender_id  # Use sender_id as client_id for compatibility
        }
        
        content = f"Action executed: {action_name}"
        if not success and error_message:
            content += f" (Error: {error_message})"
        
        try:
            unified_conversation_service.store_message(
                session_id=session_id,
                message_type=MessageType.SYSTEM,
                message=content,
                client_id=sender_id,
                metadata=metadata
            )
            logger.debug(f"Action execution tracked for {sender_id}: {action_name}")
        except Exception as e:
            logger.error(f"Failed to store action execution for {sender_id}: {e}")

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
            # Get conversation history from unified service
            messages = unified_conversation_service.get_conversation_history(session_id, limit)
            summary = unified_conversation_service.get_conversation_summary(session_id)
            
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
                'session_info': serialize_datetime(summary),
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
            # Get statistics from unified conversation service
            stats = unified_conversation_service.get_conversation_statistics()
            active_count = stats.get('active_conversations_24h', 0)
            
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
            # Use unified conversation service for cleanup
            cleaned_count = unified_conversation_service.cleanup_old_conversations(days_old=30)
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