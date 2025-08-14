"""Centralized Automatic Conversation Logger
Provides base classes and decorators for automatic conversation logging.
"""

import logging
import uuid
from typing import Any, Text, Dict, List, Optional
from .conversation_middleware import ConversationTracker, log_bot_response, log_action_execution
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# AutoLoggedAction removed - should only be used in RASA actions server
# This file is for FastAPI backend integration only

class ConversationLogger:
    """Centralized conversation logger for manual logging when needed."""
    
    @staticmethod
    def log_user_input(sender_id: str, message: str, intent: Optional[str] = None, entities: Optional[list] = None):
        """Log user input message."""
        try:
            ConversationTracker.store_user_message(
                sender_id=sender_id,
                message=message,
                intent=intent,
                entities=entities or []
            )
        except Exception as e:
            logger.error(f"Error logging user input: {e}")
    
    @staticmethod
    def log_bot_output(sender_id: str, message: str, action_name: Optional[str] = None):
        """Log bot output message."""
        try:
            log_bot_response(sender_id, message, action_name)
        except Exception as e:
            logger.error(f"Error logging bot output: {e}")
    
    @staticmethod
    def log_action(sender_id: str, action_name: str, success: bool = True, error_message: Optional[str] = None):
        """Log action execution."""
        try:
            log_action_execution(sender_id, action_name, success, error_message)
        except Exception as e:
            logger.error(f"Error logging action execution: {e}")
    
    @staticmethod
    def start_session(sender_id: Optional[str] = None) -> str:
        """Start a new conversation session and return session ID."""
        try:
            if not sender_id:
                sender_id = str(uuid.uuid4())
            
            session_id = ConversationTracker.get_or_create_session(sender_id)
            logger.info(f"Started conversation session {session_id} for sender {sender_id}")
            return session_id
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return sender_id or str(uuid.uuid4())  # Fallback to sender_id or new UUID

def auto_log_conversation(func):
    """Decorator for automatic conversation logging in FastAPI functions."""
    def wrapper(*args, **kwargs):
        try:
            # Extract sender_id if available from kwargs
            sender_id = kwargs.get('sender_id')
            
            if sender_id:
                # Log function execution
                ConversationLogger.log_action(sender_id, func.__name__)
            
            return func(*args, **kwargs)
            
        except Exception as e:
            if sender_id:
                ConversationLogger.log_action(sender_id, func.__name__, success=False, error_message=str(e))
            raise e
    
    return wrapper